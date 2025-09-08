from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session
from app.db.database import get_db
from app.db.models import Users
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_pagination_response import Page, PaginationParams, PaginationCustomParams
from app.schemas.sche_submission import SubmissionItemDetailResponse
from app.schemas.sche_upload_session import UploadSessionResponse, UploadSessionUpdateRequest, UploadSessionCreateRequest
from app.services.jwt_service import JwtService
from app.services.submission_service import SubmissionService
from app.services.upload_session_service import UploadSessionService

router = APIRouter()

# region GET Methods
@router.get("/semester_id", response_model=Page[UploadSessionResponse])
def list_sessions_by_semester(
    semester_id: int,
    pagination: PaginationCustomParams = Depends(),
    session_service: UploadSessionService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve paginated list of upload sessions in a semester (lecturer/course_leader only)."""
    sessions_paging = session_service.list_sessions_by_semester_id(
        db, pagination, semester_id, current_user.id
    )
    return sessions_paging


@router.get("/parent_session_id", response_model=Page[UploadSessionResponse])
def list_child_sessions(
    parent_session_id: int,
    pagination: PaginationCustomParams = Depends(),
    session_service: UploadSessionService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve paginated list of child upload sessions for a parent session (lecturer/course_leader only)."""
    sessions_paging = session_service.list_child_sessions_by_parent_id(
        db, pagination, parent_session_id
    )
    return sessions_paging


@router.get("/detail/{session_id}", response_model=DataResponse[UploadSessionResponse])
def get_detail(
    session_id: int,
    session_service: UploadSessionService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve upload session details by ID (lecturer/course_leader only)."""
    updated_session = session_service.get_upload_session_by_session_id(db, session_id, current_user.id)
    return DataResponse().success_response(data=updated_session)


@router.get("/{session_id}/submissions", response_model=Page[SubmissionItemDetailResponse])
def get_submissions_by_upload_session(
    session_id: int,
    params: PaginationParams = Depends(),
    submission_service: SubmissionService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve paginated list of submissions in upload session (lecturer/course_leader only)."""
    submission_paging = submission_service.get_submissions_by_session_id(
        db, params, current_user.id, session_id
    )
    return submission_paging
# endregion


# region POST Methods
@router.post("/create", response_model=DataResponse[UploadSessionResponse])
async def create_upload_session(
    request: UploadSessionCreateRequest,
    session_service: UploadSessionService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Create new upload session (lecturer/course_leader only)."""
    updated_session = await session_service.create_upload_session(db, request, current_user.id)
    return DataResponse().custom_response(
        data=updated_session,
        code="0",
        message="Add upload session successfully"
    )


@router.post("/delete", response_model=DataResponse[bool])
def delete_upload_sessions(
    session_ids: List[int],
    session_service: UploadSessionService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Delete upload sessions by IDs (lecturer/course_leader only)."""
    deleted_session = session_service.delete_list_sessions(db, session_ids, current_user.id)
    return DataResponse().custom_response(
        data=deleted_session,
        code="0",
        message="Delete upload session successfully"
    )
# endregion


# region PUT Methods
@router.put("/update", response_model=DataResponse[UploadSessionResponse])
def update_upload_session(
    request: UploadSessionUpdateRequest,
    session_service: UploadSessionService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Update upload session information (lecturer/course_leader only)."""
    updated_session = session_service.update_session_info(db, request, current_user.id)
    return DataResponse().custom_response(
        data=updated_session,
        code="0",
        message="Update upload session successful"
    )


@router.put("/hide", response_model=DataResponse[bool])
def hides_upload_sessions(
    session_ids: List[int],
    session_service: UploadSessionService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Hide upload sessions by IDs (lecturer/course_leader only)."""
    deleted_session = session_service.hide_sessions(db, session_ids, current_user.id)
    return DataResponse().custom_response(
        data=deleted_session,
        code="0",
        message="Hide sessions successfully"
    )


@router.put("/visible", response_model=DataResponse[bool])
def visibles_upload_sessions(
    session_ids: List[int],
    session_service: UploadSessionService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Visibles upload sessions by IDs (lecturer/course_leader only)."""
    deleted_session = session_service.visible_sessions(db, session_ids, current_user.id)
    return DataResponse().custom_response(
        data=deleted_session,
        code="0",
        message="Visible sessions successfully"
    )
# endregion