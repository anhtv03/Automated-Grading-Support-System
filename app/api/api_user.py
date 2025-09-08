from typing import List, Any

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Users
from app.helpers.login_manager import login_required, PermissionRequired
from app.schemas.sche_api_response import DataResponse, ResponseSchemaBase
from app.schemas.sche_pagination import PaginatedResponse
from app.schemas.sche_pagination_response import PaginationCustomParams
from app.schemas.sche_user import (
    UserResponse,
    UserItemResponse,
    UserRequest,
    UserInformation,
    UserClassification,
    UpdateUserStatusRequest,
    UpdateUserRoleRequest,
    ListUserIdDelete
)
from app.services.jwt_service import JwtService
from app.services.user_service import UserService, get_user_by_id

router = APIRouter()


# region GET Methods
@router.get("/detail/{user_id}", dependencies=[Depends(login_required)], response_model=DataResponse[UserResponse])
async def get_user_information(
        user_id: int,
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve user information by ID."""
    user: UserResponse = get_user_by_id(db, user_id)
    user.roles = UserService.get_role_by_user_id(db, user_id)
    return DataResponse().custom_response(
        code='0',
        message='Get user successfully',
        data=user
    )


@router.get("/get-list", response_model=DataResponse[PaginatedResponse[UserResponse]])
async def get_list_user(
        params: PaginationCustomParams = Depends(),
        user: Users = Depends(JwtService.validate_token),
        db: Session = Depends(get_db)
) -> Any:
    """Retrieve list of all users."""
    users = UserService.get_other_users(db, params, user.id)
    return DataResponse().custom_response(
        code="0",
        message="Get all users successfully",
        data=users
    )


@router.get("/classify-emails", response_model=DataResponse[PaginatedResponse[UserClassification]])
async def classify_emails(
        # page_index: int = 1,
        # page_size: int = 10,
        # search_text: str = "",
        # sort_by: str = "email",
        # order: str = "asc",
        params: PaginationCustomParams = Depends(),
        db: Session = Depends(get_db),
        user_service: UserService = Depends()
) -> Any:
    """Retrieve list of all classify email. (admin only)"""
    data_api = await user_service.classify_email(db, params)
    return DataResponse().custom_response(
        code='0',
        message='Get all email from API successfully',
        data=data_api
    )


# region POST Methods
@router.post("/create", dependencies=[Depends(PermissionRequired('admin'))], response_model=DataResponse)
async def create_user(
        background_tasks: BackgroundTasks,
        user: List[UserInformation],
        db: Session = Depends(get_db)
) -> Any:
    """create new user (admin only)"""
    background_tasks.add_task(UserService.create_user, db, user)
    return DataResponse().custom_response(
        code='0',
        message='Create user successfully',
        data=None
    )


@router.post("/delete", dependencies=[Depends(PermissionRequired('admin'))])
async def delete_user(
        request: ListUserIdDelete,
        db: Session = Depends(get_db)
) -> Any:
    """Update user status (admin only)."""
    deleted_count = UserService.delete_user_by_ids(db, request)
    return ResponseSchemaBase().custom_response(
        code="0",
        message=f"Deleted {deleted_count} deactive user(s) successfully."
    )


# endregion


# region PUT Methods
@router.put("/update/information", dependencies=[Depends(login_required)], response_model=DataResponse[None])
async def update_user_information(
        user_information: UserRequest,
        db: Session = Depends(get_db),
        current_user: Users = Depends(JwtService.validate_token),
        user_service: UserService = Depends()
) -> Any:
    """Update user information."""
    user_service.update_user_information(db, current_user.id, user_information)
    return DataResponse().custom_response(
        code='0',
        message='Update user information successfully',
        data=None
    )


@router.put("/remove", dependencies=[Depends(PermissionRequired('admin'))],
            response_model=DataResponse[UserItemResponse])
async def remove_user(
        user_id: int,
        db: Session = Depends(get_db),
        user_service: UserService = Depends()
) -> Any:
    """Delete user by user ID (admin only)."""
    updated_user = user_service.delete_user(db, user_id)
    return DataResponse().custom_response(
        code="0",
        message="Delete user successfully",
        data=updated_user
    )


@router.put("/update/status", dependencies=[Depends(PermissionRequired('admin'))])
async def update_status(
        request: UpdateUserStatusRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Update user status (admin only)."""
    updated_count = UserService.update_users_status(db, request.user_ids, request.message, request.status)
    return DataResponse().custom_response(
        code="0",
        message=f"Updated {updated_count} users successfully.",
        data=updated_count
    )


@router.put("/update/role", dependencies=[Depends(PermissionRequired('admin'))])
async def update_roles(
        request: UpdateUserRoleRequest,
        db: Session = Depends(get_db)
) -> Any:
    """Update user role (admin only)."""
    updated_count = UserService.update_users_role(db, request.user_ids, request.role_id)
    return DataResponse().custom_response(
        code="0",
        message=f"Updated {updated_count} users successfully.",
        data=updated_count
    )
# endregion
