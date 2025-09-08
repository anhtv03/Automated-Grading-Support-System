from typing import List

from sqlalchemy.orm import Session

from app.constants.status import SemesterStatus, UploadSessionStatus
from app.db.db_exam import db_create_exam, db_get_exams_by_name, db_get_query_exams_by_session_id, db_update_exam, \
    db_get_exam_by_user_and_semester_generate, get_exam_by_grading_guide_id, get_exam_by_ids, db_update_exams
from app.db.db_exam import db_get_exam_by_id
from app.db.db_exam_guide_history import db_create_exam_guide_history
from app.db.db_grading_guide import get_grading_guide_by_id
from app.db.models import Exam, ExamGuideHistory
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_exam import ExamRequest, ExamResponse, ExamUpdatedRequest, ExamGuideRequest
from app.schemas.sche_pagination_response import PaginationCustomParams, paginate_advanced


class ExamService:

    @staticmethod
    async def create_exam(request: ExamRequest, db: Session) -> ExamResponse:
        try:
            name_search = db_get_exams_by_name(db, request)

            if name_search:
                raise CustomException(ErrorCode.EXAM_NAME_EXIST)

            exam = Exam(
                name=request.name,
                session_id=request.session_id,
                status=SemesterStatus.VISIBLE
            )

            result = await db_create_exam(db, exam)

            return ExamResponse.model_validate(result)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def import_exam(
            exam_guide: ExamGuideRequest,
            db: Session
    ):
        try:
            exam = db_get_exam_by_id(db, exam_guide.exam_id)
            if not exam:
                raise CustomException(ErrorCode.EXAM_NOT_FOUND)

            guide = get_grading_guide_by_id(db, exam_guide.grading_guide_id)
            if not guide:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            new_exam_guide = ExamGuideHistory(
                exam_id=exam_guide.exam_id,
                grading_guide_id=exam_guide.grading_guide_id
            )

            result = db_create_exam_guide_history(db, new_exam_guide)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)


    @staticmethod
    def get_exam_by_session_id(
            db: Session,
            params: PaginationCustomParams,
            session_id: int
    ):
        try:
            query = db_get_query_exams_by_session_id(db, session_id)
            if params.keyword:
                query = query.filter(Exam.name.ilike(f"%{params.keyword}%"))

            return paginate_advanced(model=Exam, query=query, params=params)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_exam(request: ExamUpdatedRequest, db: Session) -> ExamResponse:
        try:
            exam_data = ExamRequest(
                name=request.name,
                session_id=request.session_id
            )

            if db_get_exams_by_name(db, exam_data):
                raise CustomException(ErrorCode.EXAM_NAME_EXIST)

            exam = db_get_exam_by_id(db, request.id)
            exam.name = request.name

            updated_exam = db_update_exam(db, exam)

            return ExamResponse.model_validate(updated_exam)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_exams_by_user_id(
            user_id: int,
            db: Session
    ) -> List[ExamResponse]:
        try:
            result = []
            exams = db_get_exam_by_user_and_semester_generate(db, user_id)
            if not exams:
                raise CustomException(ErrorCode.EXAM_NOT_FOUND)

            for item in exams:
                result.append(ExamResponse.model_validate(item))

            return result
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_exams_by_grading_guide_id(
            guide_id: int,
            db: Session
    ):
        try:
            exam = get_exam_by_grading_guide_id(db, guide_id)
            if not exam:
                raise CustomException(ErrorCode.EXAM_NOT_FOUND)

            return ExamResponse.model_validate(exam)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def hide_exams(
            exam_ids: List[int],
            db: Session
    ):
        try:
            exams = get_exam_by_ids(db, exam_ids)
            if len(exams) != len(exam_ids):
                raise CustomException(ErrorCode.EXAM_NOT_FOUND)

            for exam in exams:
                if exam.status == UploadSessionStatus.VISIBLE:
                    exam.status = UploadSessionStatus.HIDDEN

            db_update_exams(db, exams)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def visible_exams(
            exam_ids: List[int],
            db: Session
    ):
        try:
            exams = get_exam_by_ids(db, exam_ids)
            if len(exams) != len(exam_ids):
                raise CustomException(ErrorCode.EXAM_NOT_FOUND)

            for exam in exams:
                if exam.status == UploadSessionStatus.HIDDEN:
                    exam.status = UploadSessionStatus.VISIBLE

            db_update_exams(db, exams)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
