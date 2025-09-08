from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr, field_validator

from app.schemas.sche_role import RoleResponse


class UserBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class UserRequest(UserBase):
    email: EmailStr = Field(max_length=50)
    full_name: str


class UserResponse(UserBase):
    id: int
    email: str
    full_name: str
    status: str
    roles: RoleResponse


class UserItemResponse(UserBase):
    id: int
    email: str
    full_name: str
    status: str


class UserInformation(UserBase):
    email: EmailStr = Field(max_length=100)
    full_name: str = Field(max_length=100)
    role_id: int

    @field_validator("email")
    def check_email_domain(cls, value):
        if not value.endswith("@fpt.edu.vn"):
            raise ValueError("Email must belong to @fpt.edu.vn domain")
        return value


class OTPVerificationRequest(UserBase):
    email: EmailStr = Field(max_length=50)
    otp: str = Field(min_length=6, max_length=6)


class PasswordResetRequest(UserBase):
    email: EmailStr = Field(max_length=100)
    new_password: str = Field(min_length=8, max_length=50)


class PasswordChangeRequest(UserBase):
    email: EmailStr = Field(max_length=100)
    old_password: str = Field(min_length=8, max_length=50)
    new_password: str = Field(min_length=8, max_length=50)


class UserChangeStatusRequest(UserBase):
    id: int
    status: str


class UpdateUserStatusRequest(BaseModel):
    user_ids: List[int]
    message: str
    status: str


class UpdateUserRoleRequest(BaseModel):
    user_ids: List[int]
    role_id: int


class UserClassification(UserBase):
    email: str
    full_name: str
    status: str
    created_at: Optional[datetime]

class ListUserIdDelete(UserBase):
    user_ids: List[int]
