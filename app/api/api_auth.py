import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Body, Request, BackgroundTasks
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.constants.status import Status
from app.core.config import settings
from app.db import db_role
from app.db.database import get_db
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_api_response import DataResponse
from app.schemas.sche_auth import LoginRequest, LoginResponse, CodeRequest, RefreshTokenRequest
from app.schemas.sche_user import PasswordResetRequest, OTPVerificationRequest, PasswordChangeRequest, UserResponse
from app.services.auth_service import AuthService
from app.services.jwt_service import JwtService
from app.services.user_service import UserService

router = APIRouter()

# region GET Methods
@router.get("/google/login")
async def login_google(request: Request):
    """Generate Google OAuth2 authentication URL."""
    state = secrets.token_urlsafe(16)
    request.session['oauth_state'] = state

    redirect_uri = f"{settings.FRONTEND_URL}/google/callback"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }

    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return {"auth_url": url}

@router.get("/decode-token", response_model=DataResponse[UserResponse])
async def verify_otp_update_email(
        token: str,
        db: Session = Depends(get_db)
):
    """Decode token process."""
    user_respone = UserService.decode_token_user(db, token)
    return DataResponse().custom_response(
        code='0',
        message='Decode token successfully',
        data=user_respone
    )
# endregion

# region POST Methods
@router.post("/login", response_model=DataResponse[LoginResponse])
async def login_for_access_token(
    login_request: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user with email and password."""
    token: LoginResponse = AuthService.login(db, login_request)
    return DataResponse().custom_response(
        code='0',
        message='Login successfully',
        data=token
    )


@router.post("/refresh", response_model=DataResponse[LoginResponse])
async def login_for_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Generate access token from fresh token."""
    response = JwtService.refresh(db, request.refresh_token)
    return DataResponse().custom_response(
        code='0',
        message='Get access token successfully',
        data=response
    )


@router.post("/google/valid")
async def validate_google_auth(
    request: CodeRequest,
    db: Session = Depends(get_db)
):
    """Validate Google OAuth2 authorization code and authenticate user."""
    code = request.code
    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = f"{settings.FRONTEND_URL}/google/callback"
    params = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=params, headers=headers)
        if token_res.status_code != 200:
            raise CustomException(ErrorCode.AUTH_WITH_GOOGLE_INVALID)

        token_data = token_res.json()
        token = token_data.get("access_token")
        if not token:
            raise CustomException(ErrorCode.AUTH_WITH_GOOGLE_INVALID)

        headers["Authorization"] = f"Bearer {token}"
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers=headers
        )
        userinfo = userinfo_res.json()

        email = userinfo.get("email")
        if email is None:
            raise CustomException(ErrorCode.AUTH_WITH_GOOGLE_INVALID)

    user_system = UserService.get_user_by_email(db, email)

    if user_system.status != Status.ACTIVE:
        raise CustomException(ErrorCode.AUTH_INVALID_ACCOUNT_STATUS)

    role = db_role.get_role_by_id(db, user_system.role_id)
    if not role:
        raise CustomException(ErrorCode.ACC_ROLE_INVALID)

    token_data = {
        "sub": user_system.email,
        "user_id": user_system.id,
        "role": role.name
    }
    access_token = JwtService.create_access_token(data=token_data)
    refresh_token = JwtService.create_refresh_token(data=token_data)
    login_response = LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        email=user_system.email,
        role_name=role.name
    )

    return DataResponse().custom_response(
        code='0',
        message='Login successfully',
        data=login_response
    )


@router.post("/send-otp", response_model=DataResponse)
async def send_otp_to_email(
    email: EmailStr = Body(..., max_length=50),
    db: Session = Depends(get_db),
):
    """Send OTP to email for password reset verification."""
    AuthService.send_otp_to_email(db, email)
    return DataResponse().custom_response(
        code='0',
        message='OTP sent to email successfully',
        data=None
    )


@router.post("/verify-otp", response_model=DataResponse)
async def verify_otp(
    verify_otp_form: OTPVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP for password reset process."""
    AuthService.verify_otp(db, verify_otp_form)
    return DataResponse().custom_response(
        code='0',
        message='OTP verified successfully',
        data=None
    )


@router.post("/send-otp-update-email", response_model=DataResponse)
async def send_otp_update_email(
    background_tasks: BackgroundTasks,
    email: EmailStr = Body(..., max_length=50),
    db: Session = Depends(get_db)
):
    """Send OTP to new email for email update verification."""
    background_tasks.add_task(UserService.send_otp_to_update_email, db, email)
    return DataResponse().custom_response(
        code='0',
        message='OTP sent to email successfully',
        data=None
    )


@router.post("/verify-otp-update-email", response_model=DataResponse)
async def verify_otp_update_email(
    verify_otp_form: OTPVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP for email update process."""
    UserService.verify_otp_to_update_email(db, verify_otp_form)
    return DataResponse().custom_response(
        code='0',
        message='OTP verified successfully',
        data=None
    )
# endregion


# region PUT Methods
@router.put("/change-password", response_model=DataResponse)
async def change_password(
    password_change: PasswordChangeRequest,
    db: Session = Depends(get_db),
):
    """Change user password with current password verification."""
    AuthService.change_user_password(db, password_change)
    return DataResponse().custom_response(
        code='0',
        message='Password changed successfully',
        data=None
    )
# endregion


# region PATCH Methods
@router.patch("/reset-password", response_model=DataResponse)
async def reset_password(
    reset_password_form: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Reset user password with OTP verification."""
    AuthService.update_user_password(db, reset_password_form)
    return DataResponse().custom_response(
        code='0',
        message='Reset password successfully',
        data=None
    )
# endregion