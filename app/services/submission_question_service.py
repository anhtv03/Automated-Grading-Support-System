import re
from typing import List, Any

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.db.db_answer_template import get_all_answer_template_by_session_id
from app.db.db_criteria import db_get_criteria_by_grading_guide_id
from app.db.db_grading_guide import get_grading_guide_by_id
from app.db.db_score_history import get_score_history, db_update_score_histories, get_score_histories
from app.db.db_submission import get_all_submissions_by_session_id, db_get_submission_by_id, db_update_submissions, \
    get_submissions_by_submission_ids
from app.db.db_submission_question import (get_submission_question_by_submission_and_question_name,
                                           save_submission_question, get_submission_questions_by_exam_id,
                                           update_submission_question_cluster_id,
                                           get_submission_question_by_sub_id, create_submission_questions,
                                           db_get_score_history_by_submission_id, get_submission_questions_id,
                                           db_update_submission_question_comments)
from app.db.db_upload_session import get_upload_session_by_id
from app.db.models import SubmissionQuestion, ScoreHistory
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_criteria import CriteriaResponse
from app.schemas.sche_submisson_question import SubmissionQuestionCreateRequest, SubmissionQuestionUpdateRequest, \
    CriteriaHistoryUpdateRequest
from app.utils.word_util import get_number_of_question_by_content


class QuestionService:

    @staticmethod
    async def save_submission_question(db: Session, request: SubmissionQuestionCreateRequest):
        try:
            save_submission = save_submission_question(db, request)
            return save_submission
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def get_by_session_id(db: Session, session_id: int):
        try:
            return get_submission_questions_by_exam_id(db, session_id)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def update_cluster_id(db: Session, request: SubmissionQuestionUpdateRequest):
        try:
            return update_submission_question_cluster_id(db, request)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def get_submission_question_by_question_name(db: Session, sub_id: int, question_name: str):
        try:
            return get_submission_question_by_submission_and_question_name(db, sub_id, question_name)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def get_submission_question_by_submission_id(db: Session, question_id: int):
        result = get_submission_question_by_sub_id(db, question_id)
        if not result:
            raise CustomException(ErrorCode.SUBM_QUESTION_NOT_FOUND)
        return result

    @staticmethod
    def create_questions(session_id: int, db: Session):
        try:
            answer_template = get_all_answer_template_by_session_id(db, session_id)
            if not answer_template:
                raise CustomException(ErrorCode.EXAM_TEMPLATE_NOT_FOUND)

            number_question = get_number_of_question_by_content(answer_template.content)
            submissions = get_all_submissions_by_session_id(db, session_id)

            submission_questions = []
            for submission in submissions:
                question_pattern = r"Question (\d+)\s*(?:\([^)]+\))?:\s*(.*?)(?=(?:Question \d+|$\n*))"
                found_questions = re.findall(question_pattern, submission.content, re.DOTALL)

                question_contents = {}
                for question_num, question_content in found_questions:
                    question_contents[int(question_num)] = question_content.strip()

                for question_num in range(1, number_question + 1):
                    question_name = f"Question {question_num}"
                    content = question_contents.get(question_num, "")

                    submission_question = SubmissionQuestion(
                        submission_id=submission.id,
                        question_name=question_name,
                        content=content,
                        cluster_id=None
                    )
                    submission_questions.append(submission_question)

            create_submission_questions(db, submission_questions)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def count_number_questions(html: str) -> int:
        soup = BeautifulSoup(html, 'html.parser')
        question_tags = soup.find_all(text=re.compile(r'(?i)^question\s*\d+'))
        return len([q for q in question_tags if re.match(r'(?i)^question\s*\d+', q)])

    @staticmethod
    def get_criteria_history_by_submission_id(submission_id: int, db: Session) -> Any:
        try:
            submission = db_get_submission_by_id(db, submission_id)
            if not submission:
                raise CustomException(ErrorCode.SUBM_SUBMISSION_NOT_FOUND)

            result = db_get_score_history_by_submission_id(db, submission_id)
            return result
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_criteria_by_grading_guide_id(grading_guide_id: int, db: Session) -> List[CriteriaResponse]:
        try:
            result = []
            grading_guide = get_grading_guide_by_id(db, grading_guide_id)
            if not grading_guide:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            criteries = db_get_criteria_by_grading_guide_id(db, grading_guide_id)
            for criteria in criteries:
                result.append(CriteriaResponse.model_validate(criteria))

            return result
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_submission_question_score(
            request: List[CriteriaHistoryUpdateRequest],
            db: Session
    ):
        try:
            submission_questions: List[SubmissionQuestion] = []
            score_histories: List[ScoreHistory] = []

            # retrieve submission question data
            for question in request:
                question_existed = get_submission_questions_id(db, question.question_id)
                if not question_existed:
                    raise CustomException(ErrorCode.SUBM_QUESTION_NOT_FOUND)

                question_existed.expert_comment = question.expert_comment
                submission_questions.append(question_existed)

                # retrieve score history data
                for score_history in question.criteria:
                    criteria_history = get_score_history(db, question.question_id, score_history.criteria_id)
                    if not criteria_history:
                        raise CustomException(ErrorCode.SUBM_SCORE_HISTORY_NOT_FOUND)

                    criteria_history.expert_score = score_history.expert_score
                    score_histories.append(criteria_history)

            # update data
            db_update_score_histories(db, score_histories)
            db_update_submission_question_comments(db, submission_questions)

            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_submission_score(
            submission_ids: List[int],
            db: Session
    ):
        try:
            submission_existed = get_submissions_by_submission_ids(db, submission_ids)
            if len(submission_existed) != len(submission_ids):
                raise CustomException(ErrorCode.SUBM_SUBMISSION_NOT_FOUND)

            for submission in submission_existed:
                total_score = 0

                submission_questions = get_submission_question_by_sub_id(db, submission.id)
                for submission_question in submission_questions:
                    score_histories = get_score_histories(db, submission_question.id)

                    question_score = 0
                    for score_history in score_histories:
                        question_score += score_history.expert_score

                    total_score += question_score

                submission.final_score = total_score

            db_update_submissions(db, submission_existed)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_submission_score_by_session_id(session_id: int, db: Session):
        try:
            session = get_upload_session_by_id(db, session_id)
            if not session:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)

            submission_existed = get_all_submissions_by_session_id(db, session_id)
            if not submission_existed:
                raise CustomException(ErrorCode.SUBM_SUBMISSION_NOT_FOUND)

            for submission in submission_existed:
                total_score = 0

                submission_questions = get_submission_question_by_sub_id(db, submission.id)
                for submission_question in submission_questions:
                    score_histories = get_score_histories(db, submission_question.id)

                    question_score = 0
                    for score_history in score_histories:
                        question_score += 0 if score_history.expert_score is None else score_history.expert_score

                    total_score += question_score

                submission.final_score = total_score

            db_update_submissions(db, submission_existed)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
