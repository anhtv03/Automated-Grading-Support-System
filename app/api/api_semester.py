from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session

from app.db.database import get_db
from app.db.models import Users
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_pagination_response import Page, PaginationCustomParams
from app.schemas.sche_semester import SemesterUpdateRequest, SemesterCreateRequest, SemesterResponse
from app.services.jwt_service import JwtService
from app.services.semester_service import SemesterService

router = APIRouter()

# ======================================================================================================================
# Semester Management APIs
# ======================================================================================================================

@router.get("/lists", response_model=Page[SemesterResponse])
def get_semesters(
    params: PaginationCustomParams = Depends(),
    semester_service: SemesterService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve paginated list of all semesters (lecturer/course_leader only)."""
    semesters_paging = semester_service.get_semesters_by_user_id(db, params, current_user.id)
    return semesters_paging

@router.post("/create", response_model=DataResponse[SemesterResponse])
async def create_semester(
    request: SemesterCreateRequest,
    semester_service: SemesterService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Create new semester (lecturer/course_leader only)."""
    semester = await semester_service.create_semester(db, request, current_user.id)
    return DataResponse().custom_response(
        code="0",
        message="Add semester success",
        data=semester
    )

@router.put("/update", response_model=DataResponse[SemesterResponse])
def update_semester(
    request: SemesterUpdateRequest,
    semester_service: SemesterService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Update semester information (lecturer/course_leader only)."""
    semester = semester_service.update_semester_info(db, request, current_user.id)
    return DataResponse().custom_response(
        code="0",
        message="Successful semester update",
        data=semester
    )

@router.put("/delete", response_model=DataResponse[bool])
def delete_semester(
    semester_ids: List[int],
    semester_service: SemesterService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Delete semester by session ID (lecturer/course_leader only)."""
    deleted_semester = semester_service.delete_semesters(db, semester_ids, current_user.id)
    return DataResponse().custom_response(
        code="0",
        message="Delete semester successfully",
        data=deleted_semester
    )

@router.put("/hide", response_model=DataResponse[bool])
def hide_semester(
    semester_ids: List[int],
    semester_service: SemesterService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Hide semester by session ID (lecturer/course_leader only)."""
    hide_semester = semester_service.hide_semester(db, semester_ids, current_user.id)
    return DataResponse().custom_response(
        code="0",
        message="Hide semester success",
        data=hide_semester
    )

@router.put("/visible", response_model=DataResponse[bool])
def visible_semester(
    semester_ids: List[int],
    semester_service: SemesterService = Depends(),
    current_user: Users = Depends(JwtService.validate_token),
    db: Session = Depends(get_db)
) -> Any:
    """Visible semester by session ID (lecturer/course_leader only)."""
    visible_semester = semester_service.visible_semester(db, semester_ids, current_user.id)
    return DataResponse().custom_response(
        code="0",
        message="Visible semester success",
        data=visible_semester
    )