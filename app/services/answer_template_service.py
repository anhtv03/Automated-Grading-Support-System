from sqlalchemy.orm import Session

from app.db import db_answer_template
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_exam_template import AnswerTemplateResponse


class AnswerTemplateService:

    def get_exam_template_by_session_id(
            session_id: int,
            db: Session
    ) -> AnswerTemplateResponse:
        try:
            search_template = db_answer_template.get_all_answer_templates_by_session_id(db, session_id)

            if not search_template:
                raise CustomException(ErrorCode.EXAM_TEMPLATE_NOT_FOUND)
            else:
                return search_template[0]
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
