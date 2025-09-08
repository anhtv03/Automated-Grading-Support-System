from typing import List

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.constants.status import UploadSessionStatus
from app.db.db_exam_guide_history import db_get_guide_exam_data, db_delete_exam_data
from app.db.db_exam_question import db_get_exam_question_by_ids
from app.db.db_grading_guide import get_grading_guide_by_id
from app.db.db_guide_question import db_get_grading_guide_question_by_question_id, db_get_grading_guide_question_by_ids, \
    db_update_grading_guide_questions, db_get_grading_guide_question_by_id, db_update_grading_guide_question, \
    db_create_grading_guide_question, db_get_grading_guide_question_by_grading_guide_id, \
    db_delete_grading_guide_questions
from app.db.models import GradingGuideQuestion
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_grading_guide_question import GradingGuideQuestionResponse, GuideQuestionRequestParams, \
    GuideQuestionUpdateRequest, GuideQuestionCreateRequest
from app.schemas.sche_pagination_response import parse_key_to_filters


class GuideQuestionService:

    @staticmethod
    def get_grading_guide_question_by_exam_question_id(
            db: Session,
            params: GuideQuestionRequestParams,
            exam_question_id: int,
            grading_guide_id: int
    ) -> List[GradingGuideQuestionResponse]:
        try:
            result = []
            query = db_get_grading_guide_question_by_question_id(db, exam_question_id, grading_guide_id)

            if params.options:
                filters = parse_key_to_filters(GradingGuideQuestion, params.options)
                for f in filters:
                    query = query.filter(f)

            if hasattr(GradingGuideQuestion, params.sort_by):
                direction = desc if params.order == 'desc' else asc
                query = query.order_by(direction(getattr(GradingGuideQuestion, params.sort_by)))

            for item in query:
                result.append(GradingGuideQuestionResponse.model_validate(item))

            return result
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_grading_guide_question_by_grading_guide_id(
            db: Session,
            params: GuideQuestionRequestParams,
            grading_guide_id: int,
    ) -> List[GradingGuideQuestionResponse]:
        try:
            result = []
            query = db_get_grading_guide_question_by_grading_guide_id(db, grading_guide_id)

            if params.options:
                filters = parse_key_to_filters(GradingGuideQuestion, params.options)
                for f in filters:
                    query = query.filter(f)

            if hasattr(GradingGuideQuestion, params.sort_by):
                direction = desc if params.order == 'desc' else asc
                query = query.order_by(direction(getattr(GradingGuideQuestion, params.sort_by)))

            for item in query:
                result.append(GradingGuideQuestionResponse.model_validate(item))

            return result
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def hide_guide_question(
            guide_question_ids: List[int],
            db: Session
    ) -> bool:
        try:
            guide_question = db_get_grading_guide_question_by_ids(db, guide_question_ids)
            if len(guide_question) != len(guide_question_ids):
                raise CustomException(ErrorCode.GUIDE_QUESTION_NOT_FOUND)

            for item in guide_question:
                if item.status == UploadSessionStatus.VISIBLE:
                    item.status = UploadSessionStatus.HIDDEN

            db_update_grading_guide_questions(db, guide_question)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def visible_guide_question(
            guide_question_ids: List[int],
            db: Session
    ) -> bool:
        try:
            guide_question = db_get_grading_guide_question_by_ids(db, guide_question_ids)
            if len(guide_question) != len(guide_question_ids):
                raise CustomException(ErrorCode.GUIDE_QUESTION_NOT_FOUND)

            for item in guide_question:
                if item.status == UploadSessionStatus.HIDDEN:
                    item.status = UploadSessionStatus.VISIBLE

            db_update_grading_guide_questions(db, guide_question)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_guide_question(
            guide_question_id: int,
            new_guide_question: GuideQuestionUpdateRequest,
            db: Session
    ) -> GradingGuideQuestionResponse:
        try:
            guide_question_exited = db_get_grading_guide_question_by_id(db, guide_question_id)
            if not guide_question_exited:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            guide_question_exited.input_prompt = new_guide_question.input_prompt
            if new_guide_question.content:
                guide_question_exited.content = new_guide_question.content

            result = db_update_grading_guide_question(db, guide_question_exited)
            return GradingGuideQuestionResponse.model_validate(result)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def delete_guide_exam(db: Session, guide_id: int, exam_id: int) -> int:
        try:
            guide_exam_search = db_get_guide_exam_data(db, guide_id, exam_id)

            if not guide_exam_search:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            guide_question = db_get_grading_guide_question_by_grading_guide_id(db, guide_id)
            if guide_question:
                db_delete_grading_guide_questions(db, guide_question)

            db_delete_exam_data(db, guide_exam_search)
            return 1
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def create_guide_question(
            request: GuideQuestionCreateRequest,
            db: Session
    ):
        try:
            grading_guide = get_grading_guide_by_id(db, request.grading_guide_id)
            if not grading_guide:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            result = []
            new_guide_questions = db_get_exam_question_by_ids(db, request.exam_question_ids)
            for item in new_guide_questions:
                new_guide_question = GradingGuideQuestion(
                    grading_guide_id=grading_guide.id,
                    exam_question_id=item.id,
                    question_name=item.question_name,
                    status=UploadSessionStatus.VISIBLE,
                )
                guide_question = db_create_grading_guide_question(db, new_guide_question)
                result.append(GradingGuideQuestionResponse.model_validate(guide_question))

            return result
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def delete_grading_guide_question(db: Session, guide_question_ids: List[int]) -> int:
        try:
            grading_guide_questions = db_get_grading_guide_question_by_ids(db, guide_question_ids)
            if len(grading_guide_questions) != len(guide_question_ids):
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            db_delete_grading_guide_questions(db, grading_guide_questions)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
