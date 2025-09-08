from typing import List

from sqlalchemy.orm import Session

from app.constants.status import SemesterStatus
from app.db.db_semester import (get_semesters, create_semester, get_semester_by_user_id, delete_semesters,
                                update_semester_info, get_semester_by_name, get_semesters_by_semester_ids,
                                save_semesters)
from app.db.models import Semester
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_pagination_response import PaginationCustomParams, paginate_advanced
from app.schemas.sche_semester import SemesterCreateRequest, SemesterResponse, SemesterUpdateRequest


class SemesterService:

    @staticmethod
    def get_semesters_by_user_id(db: Session, params: PaginationCustomParams, user_id: int):
            query = get_semesters(db, user_id)
            if params.keyword:
                query = query.filter(Semester.name.ilike(f"%{params.keyword}%"))
            return paginate_advanced(model=Semester, query=query, params=params)


    @staticmethod
    async def create_semester(db: Session, request: SemesterCreateRequest, user_id: int) -> SemesterResponse:
        try:
            upload_session = get_semester_by_name(db, request.name, user_id, request.type)
            if upload_session is not None:
                raise CustomException(ErrorCode.SEM_SEMESTER_NAME_EXIST)
            new_semester = Semester(
                name=request.name,
                status=SemesterStatus.VISIBLE,
                user_id=user_id,
                type=request.type
            )
            new_upload_session = create_semester(db, new_semester)
            return SemesterResponse.model_validate(new_upload_session)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_semester_info(db: Session, semester_request: SemesterUpdateRequest, user_id: int) -> SemesterResponse:
        try:
            semester = get_semester_by_user_id(db, semester_request.id, user_id)
            if not semester:
                raise CustomException(ErrorCode.SEM_SEMESTER_NOT_FOUND)

            exist_semester_name = get_semester_by_name(db, semester_request.name, user_id, semester_request.type)

            if exist_semester_name is not None and exist_semester_name.id != semester_request.id:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NAME_HAS_EXITS)

            if semester_request.status not in SemesterStatus._value2member_map_:
                raise CustomException(ErrorCode.SEM_STATUS_INVALID)

            semester.name = semester_request.name
            semester.status = semester_request.status
            semester.type = semester_request.type
            update_semester_info(db, semester)
            return SemesterResponse.model_validate(semester)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def hide_semester(db: Session, semester_ids: List[int], user_id: int) -> bool:
        try:
            semesters = get_semesters_by_semester_ids(db, semester_ids, user_id)
            if len(semesters) != len(semester_ids):
                raise CustomException(ErrorCode.SEM_SEMESTER_NOT_FOUND)
            for semester in semesters:
                semester.status = SemesterStatus.HIDDEN
            save_semesters(db, semesters)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def visible_semester(db: Session, semester_ids: List[int], user_id: int) -> bool:
        try:
            semesters = get_semesters_by_semester_ids(db, semester_ids, user_id)
            if len(semesters) != len(semester_ids):
                raise CustomException(ErrorCode.SEM_SEMESTER_NOT_FOUND)
            for semester in semesters:
                semester.status = SemesterStatus.VISIBLE
            save_semesters(db, semesters)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def delete_semesters(db: Session, semester_ids: List[int], user_id: int) -> bool:
        try:
            semesters = get_semesters_by_semester_ids(db, semester_ids, user_id)
            if len(semesters) != len(semester_ids):
                raise CustomException(ErrorCode.SEM_SEMESTER_NOT_FOUND)
            delete_semesters(db, semesters)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
