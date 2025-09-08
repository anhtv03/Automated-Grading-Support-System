import re

from sqlalchemy.orm import Session

from app.db.db_criteria import db_get_criteria_by_grading_guide_id
from app.db.db_grading_guide import get_grading_guide_by_id
from app.db.db_score_history import db_create_score_history
from app.db.db_submission_question import get_sub_question_by_sub_id
from app.db.models import ScoreHistory
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_score_history import ScoreHistoryCreateResponse


class ScoreHistoryService:

    @staticmethod
    def create_score_history(
            request: ScoreHistoryCreateResponse,
            db: Session
    ):
        try:
            grading_guide = get_grading_guide_by_id(db, request.grading_guide_id)
            if not grading_guide:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            criteria_of_grading_guide = db_get_criteria_by_grading_guide_id(db, grading_guide.id)

            result = []
            for submission_id in request.submission_ids:
                sub_questions = get_sub_question_by_sub_id(db, submission_id)
                if not sub_questions:
                    raise CustomException(ErrorCode.SUBM_QUESTION_NOT_FOUND)

                for sub_question in sub_questions:
                    match = re.search(r'\d+', sub_question.question_name)
                    if not match:
                        continue
                    sub_question_number = int(match.group())

                    for criteria in criteria_of_grading_guide:
                        if criteria.question_number == sub_question_number:
                            new_score_history = ScoreHistory(
                                question_id=sub_question.id,
                                criteria_id=criteria.id,
                            )
                            result.append(new_score_history)

            db_create_score_history(db, result)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
