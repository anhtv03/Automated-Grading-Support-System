from typing import Dict, List

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.db_score_history import get_total_score_by_submission_question_id, get_score_histories, \
    db_update_score_histories
from app.db.db_submission import (get_query_submissions_by_session_id, create_submission, get_submission_score_counts,
                                  get_all_submissions_by_session_id, get_ai_plagiarism_submissions_by_session_id,
                                  is_user_owner_of_upload_session, db_get_submission_by_id,
                                  get_submissions_by_session_id, get_statistics_grading_submision,
                                  get_submission_score_by_ai_counts)
from app.db.db_submission_question import get_sub_question_by_sub_id, get_submission_questions_id, \
    db_update_submission_question_comments
from app.db.db_upload_session import get_upload_session_by_id
from app.db.models import Submission, ScoreHistory, SubmissionQuestion
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_pagination_response import PaginationParams, paginate_mapper
from app.schemas.sche_statistic import SubmissionStatistic
from app.schemas.sche_submission import SubmissionCreate, SubmissionItemDetailResponse, SubmissionAIDetector, \
    SubmissionItemResponse
from app.schemas.sche_submisson_question import SubmissionQuestionItemResponse


class SubmissionService:
    @staticmethod
    def get_submissions_by_session_id(db: Session, params: PaginationParams, user_id: int, session_id: int):
        try:
            upload_session = is_user_owner_of_upload_session(db, session_id, user_id)
            if not upload_session:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)
            query = get_query_submissions_by_session_id(db, session_id)

            if params.keyword:
                query = query.filter(Submission.name.ilike(f"%{params.keyword}%"))

            return paginate_mapper(db=db, model=Submission, query=query, params=params,
                                   mapper=SubmissionService.map_submission)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def save_submission(db: Session, submission_create: SubmissionCreate):
        submission = Submission(
            session_id=submission_create.session_id,
            name=submission_create.name,
            file_key=submission_create.file_key,
            content=submission_create.content,
        )
        new_submission = create_submission(db, submission)
        return new_submission

    @staticmethod
    def get_by_id(db: Session, submission_id: int):
        submission = db_get_submission_by_id(db, submission_id)
        if submission is None:
            raise CustomException(ErrorCode.SUBM_SUBMISSION_NOT_FOUND)
        return submission

    @staticmethod
    def get_all_submissions_by_session_id(db: Session, session_id: int):
        upload_session = get_upload_session_by_id(db, session_id)
        if upload_session is None:
            raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)
        submissions = get_all_submissions_by_session_id(db, session_id)
        return [SubmissionItemResponse.model_validate(s) for s in submissions]

    @staticmethod
    def map_submission(db: Session, submission: Submission) -> SubmissionItemDetailResponse:
        try:
            sorted_questions = sorted(submission.submission_question, key=lambda q: q.question_name.lower())
            question_response = []

            for q in sorted_questions:
                total_score_question = get_total_score_by_submission_question_id(db, q.id)
                question_response.append(SubmissionQuestionItemResponse(
                    id=q.id,
                    question_name=q.question_name,
                    ai_score=total_score_question.ai_total_score,
                    ai_comment=q.ai_comment,
                    expert_score=total_score_question.expert_total_score,
                    expert_comment=q.expert_comment
                ))

            return SubmissionItemDetailResponse(
                id=submission.id,
                name=submission.name,
                session_id=submission.session_id,
                type=submission.type,
                file_key=submission.file_key,
                final_score=submission.final_score,
                ai_plagiarism_score=submission.ai_plagiarism_score,
                question_response=question_response
            )
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_data_statistic(
            session_id: int,
            db: Session
    ) -> Dict[str, int]:
        try:
            return get_submission_score_counts(db, session_id)  # Assuming session_id is 1 for demonstration
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_data_statistic_by_ai(
            session_id: int,
            db: Session
    ) -> Dict[str, int]:
        try:
            return get_submission_score_by_ai_counts(db, session_id)
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def count_ai_detected(
            session_id: int,
            db: Session
    ) -> SubmissionAIDetector:
        try:
            ai_count = get_ai_plagiarism_submissions_by_session_id(db, session_id)
            total_sub = get_submissions_by_session_id(db, session_id)

            submission_result = SubmissionAIDetector(
                ai_detected_count=len(ai_count),
                total_submissions=len(total_sub)
            )

            return submission_result  # Assuming session_id is 1 for demonstration

        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_submission_by_session_id(
            user_id: int,
            submission_id: int,
            db: Session = get_db
    ) -> SubmissionItemDetailResponse:
        try:
            submission_exsited = db_get_submission_by_id(db, submission_id)
            if submission_exsited is None:
                raise CustomException(ErrorCode.SUBM_SUBMISSION_NOT_FOUND)

            upload_session = is_user_owner_of_upload_session(db, submission_exsited.session_id, user_id)
            if not upload_session:
                raise CustomException(ErrorCode.PERMISSION_ACCESS_DATA)

            return SubmissionService.map_submission(db, submission_exsited)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_data_statistic_grading(
            session_id: int,
            criteria_ids: List[int],
            db: Session = get_db
    ) -> List[SubmissionStatistic]:
        try:
            session = get_upload_session_by_id(db, session_id)
            if session is None:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)

            submisstion_statistic = get_statistics_grading_submision(db, session_id, criteria_ids)
            return submisstion_statistic
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_submission_score(session_id: int, db: Session):
        try:
            upload_session = get_upload_session_by_id(db, session_id)
            if not upload_session:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)

            submissions = get_all_submissions_by_session_id(db, session_id)

            submission_question: List[SubmissionQuestion] = []
            score_histories: List[ScoreHistory] = []
            for submission in submissions:

                submission_question_existed = get_sub_question_by_sub_id(db, submission.id)
                # retrieve submission question data
                for question in submission_question_existed:
                    question_existed = get_submission_questions_id(db, question.id)
                    if not question_existed:
                        raise CustomException(ErrorCode.SUBM_QUESTION_NOT_FOUND)

                    if question_existed.expert_comment is None:
                        question_existed.expert_comment = question.ai_comment
                    submission_question.append(question_existed)

                    # retrieve score history data
                    score_history_list = get_score_histories(db, question.id)
                    for score_history in score_history_list:
                        if score_history.expert_score is None:
                            score_history.expert_score = score_history.ai_score
                            score_histories.append(score_history)

            # update data
            db_update_score_histories(db, score_histories)
            db_update_submission_question_comments(db, submission_question)

            return True
        except CustomException as e:
            raise
        except Exception as e:
            print(str(e))  # hoặc dùng repr(e) để chi tiết hơn
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
