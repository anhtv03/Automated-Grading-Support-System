from typing import List

from sqlalchemy.orm import Session

from app.constants.status import UploadSessionStatus, UploadSessionTaskStatus
from app.db.db_semester import get_semester_by_user_id
from app.db.db_upload_session import (save_upload_session, get_upload_session_by_id, get_upload_session_by_owner,
                                      query_session_by_name_semester,
                                      query_sessions_by_semester_id, update_session_info,
                                      delete_sessions, get_upload_sessions_by_session_ids, save_upload_sessions,
                                      query_child_sessions_by_parent_id, query_session_by_name_parent,
                                      )
from app.db.models import UploadSession, Submission
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_pagination_response import PaginationCustomParams, paginate_advanced
from app.schemas.sche_upload_session import (UploadSessionCreateRequest, UploadSessionResponse,
                                             UploadSessionUpdateRequest, UploadSessionUpdateTaskStatus)
from sqlalchemy import or_

class UploadSessionService:

    @staticmethod
    async def create_upload_session(db: Session, request: UploadSessionCreateRequest, user_id: int):
        try:
            type = request.type
            if (type == "child"):
                upload_session = query_session_by_name_parent(db, request.name, request.parent_session_id)
            else:
                semester = get_semester_by_user_id(db, request.semester_id, user_id)
                if not semester:
                    raise CustomException(ErrorCode.SEM_SEMESTER_NOT_FOUND)

                # check if parent session exists
                upload_session = query_session_by_name_semester(db, request.name, request.semester_id)


            if upload_session is not None:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NAME_HAS_EXITS)

            new_upload_session = UploadSession(
                name=request.name,
                semester_id=request.semester_id,
                parent_session_id=request.parent_session_id if type == "child" else None,
                status=UploadSessionStatus.VISIBLE,
                grading_status=UploadSessionTaskStatus.NOT_START,
                ai_detector_status=UploadSessionTaskStatus.NOT_START,
                plagiarism_status=UploadSessionTaskStatus.NOT_START
            )
            new_upload_session = save_upload_session(db, new_upload_session)
            return new_upload_session
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def list_sessions_by_semester_id(db: Session, pagination: PaginationCustomParams, semester_id: int, user_id: int):
        try:
            semester = get_semester_by_user_id(db, semester_id, user_id)
            if not semester:
                raise CustomException(ErrorCode.SEM_SEMESTER_NOT_FOUND)

            query = query_sessions_by_semester_id(db, semester_id)
            if pagination.keyword:
                query = query.filter(UploadSession.name.ilike(f"%{pagination.keyword}%"))
            return paginate_advanced(model=UploadSession, query=query, params=pagination)

        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def list_child_sessions_by_parent_id(db: Session, pagination: PaginationCustomParams, parent_session_id: int):
        try:
            # check if parent session exists
            session_exists = get_upload_session_by_id(db, parent_session_id)
            if not session_exists:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)

            query = query_child_sessions_by_parent_id(db, parent_session_id)
            if pagination.keyword:
                query = query.outerjoin(Submission, Submission.session_id == UploadSession.id)
                query = query.filter(
                    or_(
                        UploadSession.name.ilike(f"%{pagination.keyword}%"),
                        Submission.name.ilike(f"%{pagination.keyword}%")
                    )
                ).distinct()
            return paginate_advanced(model=UploadSession, query=query, params=pagination)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_upload_session_by_session_id(db: Session, session_id: int, user_id: int):
        try:
            print(f"session_id: {session_id} and user_id: {user_id}")
            upload_session = get_upload_session_by_owner(db, session_id, user_id)
            if upload_session is None:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)
            return upload_session
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_session_info(db: Session, request: UploadSessionUpdateRequest, user_id: int) -> UploadSessionResponse:
        try:
            upload_session = UploadSessionService.get_upload_session_by_session_id(db, request.id, user_id)
            exist_session_name = query_session_by_name_semester(db, request.name, upload_session.semester_id)

            if exist_session_name is not None and exist_session_name.id != upload_session.id:
                raise CustomException(ErrorCode.SESSION_UPLOAD_NAME_HAS_EXITS)

            if request.status not in UploadSessionStatus._value2member_map_:
                raise CustomException(ErrorCode.SESSION_UPLOAD_STATUS_INVALID)

            upload_session.status = request.status
            upload_session.name = request.name
            updated_session = update_session_info(db, upload_session)
            return UploadSessionResponse.model_validate(updated_session)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_session_task_status(db: Session, request: UploadSessionUpdateTaskStatus,
                                   user_id: int) -> UploadSessionResponse:
        try:
            upload_session = UploadSessionService.get_upload_session_by_session_id(db, request.id, user_id)

            if request.status not in UploadSessionTaskStatus._value2member_map_:
                raise CustomException(ErrorCode.SESSION_UPLOAD_TASK_STATUS_INVALID)

            upload_session.plagiarism_status = request.status
            updated_session = update_session_info(db, upload_session)
            return UploadSessionResponse.model_validate(updated_session)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_session_task_id(db: Session, session_id: int, user_id: int, type: str,task_id: str) -> UploadSessionResponse:
        try:
            upload_session = UploadSessionService.get_upload_session_by_session_id(db, session_id, user_id)
            if(type == "ai_detector"):
                upload_session.task_ai = task_id
            elif(type == "plagiarism_check"):
                upload_session.task_plagiarism = task_id
            elif (type == "grading_submission"):
                upload_session.task_grading = task_id
            updated_session = update_session_info(db, upload_session)
            return UploadSessionResponse.model_validate(updated_session)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_session_task(db: Session, session_id: int, user_id: int, type: str,
                               status: str) -> UploadSessionResponse:
        try:
            upload_session = UploadSessionService.get_upload_session_by_session_id(db, session_id, user_id)
            if (type == "ai_detector"):
                upload_session.ai_detector_status = status
            elif (type == "plagiarism_check"):
                upload_session.plagiarism_status = status
            elif (type == "grading_submission"):
                upload_session.grading_status = status
            updated_session = update_session_info(db, upload_session)
            return UploadSessionResponse.model_validate(updated_session)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def delete_list_sessions(db: Session, session_ids: List[int], user_id: int) -> bool:
        try:
            upload_sessions = get_upload_sessions_by_session_ids(db, session_ids)
            for upload_session in upload_sessions:
                semester = get_semester_by_user_id(db, upload_session.semester_id, user_id)
                if not semester:
                    raise CustomException(ErrorCode.PERMISSION_ACCESS_DATA)
            if len(upload_sessions) != len(session_ids):
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)
            delete_sessions(db, upload_sessions)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def hide_sessions(db: Session, session_ids: List[int], user_id: int) -> bool:
        try:
            upload_sessions = get_upload_sessions_by_session_ids(db, session_ids)
            if len(upload_sessions) != len(session_ids):
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)
            for upload_session in upload_sessions:
                semester = get_semester_by_user_id(db, upload_session.semester_id, user_id)
                if not semester:
                    raise CustomException(ErrorCode.PERMISSION_ACCESS_DATA)
                upload_session.status = UploadSessionStatus.HIDDEN
            save_upload_sessions(db, upload_sessions)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def visible_sessions(db: Session, session_ids: List[int], user_id: int) -> bool:
        try:
            upload_sessions = get_upload_sessions_by_session_ids(db, session_ids)
            if len(upload_sessions) != len(session_ids):
                raise CustomException(ErrorCode.SESSION_UPLOAD_NOT_FOUND)
            for upload_session in upload_sessions:
                semester = get_semester_by_user_id(db, upload_session.semester_id, user_id)
                if not semester:
                    raise CustomException(ErrorCode.PERMISSION_ACCESS_DATA)
                upload_session.status = UploadSessionStatus.VISIBLE
            save_upload_sessions(db, upload_sessions)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
