import asyncio
import json
import os
from typing import Dict, Any

import numpy as np
from celery import Celery
from fastapi import HTTPException
from scipy.sparse import csr_matrix

from app.constants.status import UploadSessionTaskStatus
from app.db.database import SessionLocal
from app.db.db_grading_guide import db_get_grading_guide_by_session_id
from app.db.db_guide_question import get_guide_questions
from app.db.db_score_history import get_score_history
from app.db.db_submission import get_all_submissions_by_session_id, db_update_submissions
from app.db.db_submission import get_submissions_by_session_id
from app.db.db_submission_question import get_submission_question_by_sub_id
from app.db.db_upload_session import get_upload_session_by_id, update_session_info
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_score_history import ScoreHistoryCreateResponse
from app.schemas.sche_submission import SubmissionResponse
from app.schemas.sche_upload_session import UploadSessionUpdateTaskStatus
from app.services.ai_detector_service import AIDetectorService
from app.services.answer_template_service import AnswerTemplateService
from app.services.file_service import FileService
from app.services.grading_service import GradingService
from app.services.plagiarism_service import PlagiarismService
from app.services.score_history_service import ScoreHistoryService
from app.services.submission_question_service import QuestionService
from app.services.submission_service import SubmissionService
from app.services.upload_session_service import UploadSessionService

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

API_KEYS = [
    "BebE636UCXLkVBLkvNLWAJivF6TRVFwSFxsGwx96400b7712",
    "LRWp6MN69akrpmnWZoTBpCFmHAK5WJoI1EOubA5C5e4d16cd",
    "cEmLcgucfoAzs2mLICbv57dSIhspaL6vg18uWIf816aee3a6",
    "bIT8FXKDd1pXS3eZONIc8CQsL8bUm68u1XjHxobx469fc348",
    "MLJwhtBlU6g0G7xD4FOy7Dk0f4g0h1AXRWSZfl3B8c1ba5fc",
    "aqh1QGE9Vxpf7xmFUd7rFX6vaZcJeIUtN3vlXsmZ339f413f",
    "RmVZoYZPbUQkzKtYbRm6AdtakCRwFezWpmuNumbl56cead34",
    "wKjpeqd8cObHMvtQ9ZmaYpLP5WBwvJAt70Qt0tXG8be5a8ca",
    "yztyp456utWh1PFWR4wQyaE9pnvK11Ifm9laT2M6ac1b0bb0",
]


@celery.task(name="ai_detector", bind=True)
def ai_detector(self, session_id: int):
    db = SessionLocal()
    try:
        session = get_upload_session_by_id(db, session_id)
        if not session:
            raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)

        submissions = get_all_submissions_by_session_id(db, session_id)
        if not submissions:
            raise CustomException(ErrorCode.SUBM_SUBMISSION_NOT_FOUND)

        total_files = len(submissions)
        updated_submissions = []
        for i, submission in enumerate(submissions):
            updated_submission = asyncio.run(AIDetectorService.detect_plagiarism(submission, api_keys=API_KEYS))
            updated_submissions.append(updated_submission)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': total_files,
                    'message': f'Processing submission {i + 1}/{total_files}'
                }
            )

        updated_submissions = db_update_submissions(db, updated_submissions)

        session.ai_detector_status = "completed"
        update_session_info(db, session)
        self.update_state(
            state='SUCCESS',
            meta={
                'current': total_files,
                'total': total_files,
                'message': f'Have done process {i + 1}/{total_files}'
            }
        )
        return {
            'data': [SubmissionResponse.model_validate(submission) for submission in updated_submissions],
            'message': f'Have done process {total_files} submission.',
            'status': 'success'
        }
    except CustomException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise CustomException(ErrorCode.COM_INTERNAL_SERVER_ERROR)
    finally:
        db.close()


@celery.task(name="run_plagiarism_check", bind=True)
def run_plagiarism_check(self, session_id: int, user_id: int):
    db = SessionLocal()
    try:
        # session = UploadSessionService.get_upload_session_by_session_id(db, session_id, user_id)
        session = get_upload_session_by_id(db, session_id)
        if not session:
            raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)
        if session.plagiarism_status == UploadSessionTaskStatus.COMPLETED:
            return DataResponse().custom_response_list(
                code="0",
                message="Have check plagiarism before",
                data=None
            )
        # if not grading or plagiarism before will insert submission question
        if (
                (session.plagiarism_status == UploadSessionTaskStatus.NOT_START)
                and (session.grading_status == UploadSessionTaskStatus.NOT_START)
                and (session.ai_detector_status == UploadSessionTaskStatus.NOT_START)
        ):
            QuestionService.create_questions(session_id, db)
        # get all submission by session_id
        submissions = SubmissionService.get_all_submissions_by_session_id(db, session_id)
        grouped = {}
        # loop submission to extract content to question {questionName: "content"}
        for i, submission in enumerate(submissions):
            blocks = submission.content.split("\n")
            questions = FileService.group_blocks_by_question(blocks)
            question_content_map = {
                q["questionName"].strip().capitalize(): q["content"]
                for q in questions
            }

            submission_questions = asyncio.run(
                QuestionService.get_submission_question_by_submission_id(db, submission.id))
            # add content into question
            for sq in submission_questions:
                qname = sq.question_name.strip().capitalize()
                content = question_content_map.get(qname, "").strip()
                if not content:
                    continue
                if qname not in grouped:
                    grouped[qname] = {
                        "question_name": qname,
                        "question_ids": [],
                        "question_content": []
                    }

                grouped[qname]["question_ids"].append(sq.id)
                grouped[qname]["question_content"].append(content)
        template = AnswerTemplateService.get_exam_template_by_session_id(session_id, db)
        template_question_map = {}
        if template:
            blocks_temp = template.content.split("\n")
            template_questions = FileService.group_blocks_by_question(blocks_temp)
            template_question_map = {
                q["questionName"]: PlagiarismService.preprocess_text(q["content"])
                for q in template_questions
            }

        total_progress = sum(len(group) for group in grouped.values())

        processed = 0
        for group in grouped.values():
            question_name = group["question_name"]
            texts = group["question_content"][:]

            if question_name in template_question_map:
                texts.append(template_question_map[question_name])
                has_template = True
            else:
                has_template = False

            cleaned_texts = [PlagiarismService.preprocess_text(t) for t in texts]
            tfidf_matrix, tfidf_model = PlagiarismService.compute_tfidf(cleaned_texts)
            if has_template:
                tfidf_matrix = subtract_template(tfidf_matrix)

            result = asyncio.run(
                PlagiarismService.cluster_and_update_documents(
                    db=db,
                    question_name=question_name,
                    tfidf_matrix=tfidf_matrix,
                    sub_ques_ids=group["question_ids"],
                    k_max=10
                )
            )
            vectors_dense = result["vectors_dense"]
            mapped_ids = result["mapped_ids"]
            used_ids = result["used_ids"]

            id_to_index = {qid: idx for idx, qid in enumerate(mapped_ids)}

            used_vectors = [vectors_dense[id_to_index[qid]] for qid in used_ids]

            filtered_matrix = np.array(used_vectors)

            plagiarism_results = asyncio.run(
                PlagiarismService.check_plagiarism_in_clusters(
                    db=db,
                    tfidf_matrix=filtered_matrix,
                    question_name=question_name,
                    sub_ques_ids=used_ids,
                    cluster_labels=result["cluster_labels"],
                    threshold=0.9
                )
            )
            processed += 1
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': processed,
                    'total': total_progress,
                    'message': f'Đang xử lý {processed}/{total_progress}'
                }
            )

        # update status upload session
        session_status = UploadSessionUpdateTaskStatus(
            id=session_id,
            status=UploadSessionTaskStatus.COMPLETED
        )
        self.update_state(
            state='SUCCESS',
            meta={
                'current': total_progress,
                'total': total_progress,
                'message': f'Đã xử lý xong check đạo văn'
            }
        )
        UploadSessionService.update_session_task_status(db, session_status, user_id)
        return True
    except Exception as e:
        db.rollback()  # Rollback on global error
        session.plagiarism_status = "failure"
        update_session_info(db, session)
        raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
    finally:
        db.close()


@celery.task(name="run_grading_submission", bind=True)
def run_grading_submission(self, session_id: int) -> Any:
    db = SessionLocal()
    try:
        session = get_upload_session_by_id(db, session_id)
        # Check if the session exists
        if not session:
            raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)

        grading_guide = db_get_grading_guide_by_session_id(db, session_id).first()
        if not grading_guide:
            raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

        submissions = get_all_submissions_by_session_id(db, session_id)
        if not submissions:
            raise CustomException(ErrorCode.SUBM_SUBMISSION_NOT_FOUND)
        submission_ids = [submission.id for submission in submissions]
        if (
                (session.plagiarism_status == UploadSessionTaskStatus.NOT_START)
                and (session.grading_status == UploadSessionTaskStatus.NOT_START)
                and (session.ai_detector_status == UploadSessionTaskStatus.NOT_START)
        ):
            QuestionService.create_questions(session_id, db)

        if (session.grading_status == UploadSessionTaskStatus.NOT_START):
            new_score_history = ScoreHistoryCreateResponse(
                grading_guide_id=grading_guide.id,
                submission_ids=submission_ids
            )
            ScoreHistoryService.create_score_history(new_score_history, db)
        # Fetch grading guide and questions

        guide_questions = get_guide_questions(db, grading_guide.id)
        guide_content_map: Dict[str, str] = {gq.question_name: gq.content for gq in guide_questions}

        criteria_map = GradingService.get_criteria_map(db, grading_guide)
        if len(guide_content_map) != len(criteria_map):
            raise CustomException(ErrorCode.COM_GUIDE_CONTENT_MISMATCH)

        # Fetch all submissions and their questions in one go
        submissions = get_submissions_by_session_id(db, session_id)
        sub_questions_map = {sub.id: get_submission_question_by_sub_id(db, sub.id) for sub in submissions}
        total_files = sum(len(qs) for qs in sub_questions_map.values())  # tổng số submission questions
        current_index = 0  # đếm số đã xử lý
        # Process submissions
        for sub_id, sub_questions in sub_questions_map.items():
            for sq in sub_questions:
                q_name = sq.question_name
                if q_name not in criteria_map or q_name not in guide_content_map:
                    continue

                criteria_list = criteria_map[q_name]
                guide_content = guide_content_map[q_name]

                try:
                    # Stringify criteria names
                    criteria_str = "\n".join(c.name for c in criteria_list if hasattr(c, 'name'))

                    # Define instruction and constraints
                    instruction = (
                        "As an expert in Software Testing, grade the submission based on the provided Grading Guide. "
                        "Strictly follow the Marking Criteria to assign points. Extract the main criteria from the "
                        "Detailed Answer and assign scores without per-criterion explanations. Base your evaluation "
                        "on trained Software Testing knowledge and the project context provided in the Question. "
                        "Your response must be EXCLUSIVELY a valid JSON object starting with '{' and ending with '}', "
                        "with no introductory text, explanations, or any other content before or after the JSON. "
                        "The \"max_score\" values in the \"criteria\" array are fixed and must not be altered under any circumstances."
                        "\"general_comment\": A concise comment (20-50 words) evaluating the submission's alignment "
                        "with the Marking Criteria and project context."
                    )

                    constraints = (
                        "Constraints:\n"
                        "- If the submission contains no data, set all criterion scores to 0 and "
                        "\"general_comment\": \"No content provided, evaluation not possible.\"\n"
                        "- For each criterion, the score MUST be <= max_score, and max_score must remain UNCHANGED from the Sample.\n"
                        "- Only modify \"score\" within \"criteria\" and \"general_comment\"; all other fields and the structure must remain identical to the Sample.\n"
                        "- Return ONLY the JSON object as shown in the Sample, with no additional text or content.\n"
                        "- The output must be pure JSON without any wrapping text, prefixes like 'Here is the JSON:', or additional lines.\n"
                        "- Strictly preserve the \"max_score\" values as provided in the Sample; any modification to \"max_score\" will invalidate the response."
                    )

                    # Generate sample JSON as string with \n, including max_score
                    sample_criteria = ",\n".join(
                        f'    {{"criterion": "{c.name}", "score": 0, "max_score": {c.max_point or 0}}}'
                        for c in criteria_list
                    )

                    sample = (
                        "Sample:\n"
                        '{\n'
                        f'  "criteria": [\n{sample_criteria}\n  ],\n'
                        '  "general_comment": ""\n'
                        '}'
                    )

                    # Build prompt
                    prompt1 = f"{instruction}\n\n{constraints}\n\n{sample}"
                    prompt2 = f"Grade the following student submission based on the provided grading guide\nGrading guide: \n{guide_content}\n\nSubmission: {sq.content if sq.content else ''}"

                    # Call AI service with retry logic
                    # max_retries = 3
                    # for attempt in range(max_retries):
                    #     result = GradingService.get_score(prompt)
                    #
                    #     # Parse JSON content from result
                    #     result_data = json.loads(result.content)
                    #
                    #     # Check if max_score is unchanged and score <= max_score
                    #     is_valid = True
                    #     for crit in criteria_list:
                    #         for criterion in result_data.get("criteria", []):
                    #             if criterion["criterion"] == crit.name:
                    #                 original_max_score = crit.max_point or 0
                    #                 if (criterion.get("score", 0) > criterion.get("max_score", 0) or
                    #                         criterion.get("max_score", 0) != original_max_score):
                    #                     is_valid = False
                    #                     break
                    #         if not is_valid:
                    #             break
                    #
                    #     if is_valid:
                    #         break
                    #     else:
                    #         print(f"Attempt {attempt + 1}/{max_retries} failed: Invalid score or max_score for question {sq.id}. Retrying...")
                    #         if attempt == max_retries - 1:
                    #             print.error(f"Max retries reached for question {sq.id}. Using default scores.")
                    #             result_data = {
                    #                 "criteria": [{"criterion": c.name, "score": 0, "max_score": c.max_point or 0}
                    #                              for c in criteria_list],
                    #                 "general_comment": "Evaluation failed after multiple retries due to invalid scoring."
                    #             }
                    result = GradingService.get_score(prompt1, prompt2)
                    result_data = json.loads(result)

                    # Update submission question
                    sq.ai_comment = result_data.get("general_comment", "")

                    # Create lookup dict for criteria scores
                    criteria_scores = {crit["criterion"]: crit.get("score", 0) for crit in
                                       result_data.get("criteria", [])}

                    # Update score history
                    for crit in criteria_list:
                        score_hist = get_score_history(db, sq.id, crit.id)
                        if score_hist and crit.name in criteria_scores:
                            score_hist.ai_score = criteria_scores[crit.name]

                except Exception as e:
                    continue
            current_index += 1
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': current_index,
                    'total': total_files,
                    'message': f'Đã xử lý xong {current_index + 1}/{total_files}'
                }
            )

        session = get_upload_session_by_id(db, session_id)
        session.grading_status = "completed"
        update_session_info(db, session)

        self.update_state(
            state='SUCCESS',
            meta={
                'current': total_files,
                'total': total_files,
                'message': f'Have process done {total_files}/{total_files}'
            }
        )
        return {
            'current': total_files,
            'total': total_files,
            'message': f'Đã xử lý xong {total_files}/{total_files}',
            'status': 'success'
        }
    except CustomException as e:
        raise e
    except Exception as e:
        db.rollback()  # Rollback on global error
        session.grading_status = "failure"
        update_session_info(db, session)
        raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)


def subtract_template(tfidf_matrix):
    if tfidf_matrix.shape[0] <= 1:
        raise HTTPException(status_code=400, detail="Insufficient documentation after removing template")

    template_vector = tfidf_matrix[-1]
    matrix_wo_template = tfidf_matrix[:-1]

    if template_vector.shape[1] != matrix_wo_template.shape[1]:
        raise HTTPException(status_code=500, detail="Shape mismatch.")

    A = matrix_wo_template.toarray()
    T = template_vector.toarray().reshape(1, -1)

    result = np.maximum(A - T, 0)
    return csr_matrix(result)
