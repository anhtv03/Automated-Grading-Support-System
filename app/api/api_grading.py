from fastapi import APIRouter

from typing import List, Any

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Users
from app.helpers.login_manager import login_required, PermissionRequired
from app.schemas.sche_api_response import DataResponse, ResponseSchemaBase
from app.schemas.sche_pagination import PaginatedResponse
from app.schemas.sche_pagination_response import PaginationCustomParams
from app.services.grading_service import GradingService

router = APIRouter()


# region POST Methods
@router.post("/", response_model=DataResponse)
async def grading_submission(
    session_id: int,
    db: Session = Depends(get_db)
) -> Any:
    GradingService.grade_submissions(db, session_id)
    return DataResponse().custom_response(
        code='0',
        message='Grading submission successfully',
        data=None
    )
# endregion