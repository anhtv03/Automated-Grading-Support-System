from typing import Optional

from pydantic import EmailStr
from pymemcache.client.base import Client
from sqlalchemy.orm import Session

from app.constants.status import Status
from app.core.config import settings
from app.db import db_role
from app.db import db_user
from app.db.db_user import (get_user_by_email, update_user_password)
from app.db.models import Users, Role
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.external.email_service import send_email_smtp
from app.schemas.sche_auth import LoginRequest, LoginResponse
from app.schemas.sche_user import (OTPVerificationRequest, PasswordResetRequest, PasswordChangeRequest)
from app.services.jwt_service import JwtService
from app.utils import user_util
from app.utils.password_util import verify_password, is_valid_password
from app.utils.security import generate_otp

memcached_client = Client((settings.MEMCACHED_HOST, settings.MEMCACHED_PORT))

class AuthService:

    @staticmethod
    def login(
            db: Session, login_request: LoginRequest
    ) -> LoginResponse:
            user: Optional[Users] = db_user.get_user_by_email(db, login_request.email)
            if not user:
                raise CustomException(ErrorCode.AUTH_EMAIL_NOT_FOUND)

            role: Optional[Role] = db_role.get_role_by_id(db, user.role_id)

            if role is None:
                raise CustomException(ErrorCode.ACC_ROLE_NOT_FOUND)

            if not verify_password(login_request.password, user.password):
                raise CustomException(ErrorCode.AUTH_INVALID_LOGIN_CREDENTIALS)

            if user.status != Status.ACTIVE:
                raise CustomException(ErrorCode.AUTH_INVALID_ACCOUNT_STATUS)

            token_data = {
                "sub": user.email,  # subject JWT
                "user_id": user.id,
                "role": role.name
            }
            access_token = JwtService.create_access_token(data=token_data)
            refresh_token = JwtService.create_refresh_token(data=token_data)

            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                email=user.email,
                role_name=role.name
            )

    @staticmethod
    def send_otp_to_email(
            db: Session,
            email: EmailStr
    ) -> bool:
        try:
            user: Optional[Users] = get_user_by_email(db, email)

            # Check valid user
            user_util.is_valid_user(user)

            otp = generate_otp()
            cache_key = F"{email}"

            try:
                memcached_client.set(
                    key=cache_key,
                    value=otp,
                    expire=180
                )
            except Exception as ex:
                raise CustomException(ErrorCode.AUTH_OTP_STORAGE_FAILED)

            result = send_email_smtp(email, otp, "otp")
            if not result:
                memcached_client.delete(cache_key)
                raise CustomException(ErrorCode.AUTH_EMAIL_SEND_FAILED)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def verify_otp(db: Session, verify_otp_form: OTPVerificationRequest) -> bool:
        try:
            user: Optional[Users] = get_user_by_email(db, verify_otp_form.email)

            # Check valid user
            user_util.is_valid_user(user)

            cache_key = F"{verify_otp_form.email}"
            try:
                stored_otp = memcached_client.get(cache_key)
            except Exception as ex:
                raise CustomException(ErrorCode.AUTH_OTP_STORAGE_FAILED)

            if stored_otp is None:
                raise CustomException(ErrorCode.AUTH_OTP_EXPIRED)
            stored_otp = stored_otp.decode('utf-8')

            if stored_otp != verify_otp_form.otp:
                raise CustomException(ErrorCode.AUTH_OTP_INVALID)
            memcached_client.delete(cache_key)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_user_password(
            db: Session,
            reset_password: PasswordResetRequest
    ) -> bool:
        try:
            user: Optional[Users] = get_user_by_email(db, reset_password.email)
            if not user:
                raise CustomException(ErrorCode.AUTH_EMAIL_NOT_FOUND)

            if not is_valid_password(reset_password.new_password):
                raise CustomException(ErrorCode.AUTH_PASSWORD_POLICY_VIOLATED)

            result = update_user_password(db, reset_password.new_password, user)
            if not result:
                raise CustomException(ErrorCode.COM_UPDATE_FAILED)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def change_user_password(
            db: Session,
            reset_password: PasswordChangeRequest
    ) -> bool:
        try:
            if reset_password.new_password == reset_password.old_password:
                raise CustomException(ErrorCode.AUTH_PASSWORD_SAME)

            user: Optional[Users] = get_user_by_email(db, reset_password.email)

            if not user:
                raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)

            if not verify_password(
                    reset_password.old_password,
                    user.password
            ):
                raise CustomException(ErrorCode.AUTH_PASSWORD_OLD_INCORRECT)

            if not is_valid_password(reset_password.new_password):
                raise CustomException(ErrorCode.AUTH_PASSWORD_POLICY_VIOLATED)

            result = update_user_password(db, reset_password.new_password, user)
            if not result:
                raise CustomException(ErrorCode.COM_UPDATE_FAILED)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
