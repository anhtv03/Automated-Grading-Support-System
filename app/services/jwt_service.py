from datetime import timedelta, datetime, timezone
from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from fastapi_sqlalchemy import db
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.constants.status import Status
from app.constants.token_type import TokenType
from app.core.config import settings
from app.db.models import Users, Role
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.db.db_user import get_user_by_id
from app.db.db_role import get_role_by_id
from app.schemas.sche_auth import LoginResponse


class JwtService:
    reusable_oauth2 = HTTPBearer(
        scheme_name='Authorization'
    )

    pwd_context = CryptContext(schemes=["sha512_crypt"], deprecated="auto")

    @staticmethod
    def validate_token(http_authorization_credentials=Depends(reusable_oauth2)) -> Users:
        """Decode JWT token to get user info (e.g., email or user_id)"""
        try:
            # Decode token
            payload = jwt.decode(
                http_authorization_credentials.credentials,
                settings.ACCESS_KEY,
                algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get('user_id')
            if user_id is None:
                raise CustomException(ErrorCode.ACC_INVALID_TOKEN)

            user = db.session.query(Users).get(user_id)
            if not user:
                raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)
            return user

        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
            )
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    def create_access_token(data: dict) -> str:
        try:
            to_encode = data.copy()
            expire = datetime.now(timezone.utc) + timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode.update({
                "exp": expire,
                "type": "access_token"
            })
            encoded_jwt = jwt.encode(to_encode, settings.ACCESS_KEY, algorithm=settings.ALGORITHM)
            return encoded_jwt
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    def create_refresh_token(data: dict) -> str:
        try:
            to_encode = data.copy()
            expire = datetime.now(timezone.utc) + timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS))
            to_encode.update({
                "exp": expire,
                "type": "refresh_token"
            })
            encoded_jwt = jwt.encode(to_encode, settings.REFRESH_KEY, algorithm=settings.ALGORITHM)
            return encoded_jwt
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def decode_jwt_token(token: str, token_type: str) -> dict:
        try:
            if token_type == TokenType.ACCESS_TOKEN:
                key = settings.ACCESS_KEY
            elif token_type == TokenType.REFRESH_TOKEN:
                key = settings.REFRESH_KEY
            else:
                raise HTTPException(status_code=400, detail="Unknown token type")
            payload = jwt.decode(
                token,
                key,
                algorithms=[settings.ALGORITHM]
            )
            return payload

        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid token")

    @staticmethod
    def refresh(db: Session, refresh_token: str) -> LoginResponse:
        payload = JwtService.decode_jwt_token(refresh_token, TokenType.REFRESH_TOKEN)
        user_id = payload.get("user_id")
        if not user_id:
            raise CustomException(ErrorCode.ACC_INVALID_TOKEN)
        user = get_user_by_id(db, user_id)
        if not user:
            raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)

        if user.status != Status.ACTIVE:
            raise CustomException(ErrorCode.AUTH_INVALID_ACCOUNT_STATUS)

        role: Optional[Role] = get_role_by_id(db, user.role_id)

        if role is None:
            raise CustomException(ErrorCode.ACC_ROLE_NOT_FOUND)

        token_data = {
            "sub": user.email,
            "user_id": user.id,
            "role": role.name
        }
        access_token = JwtService.create_access_token(data=token_data)
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            email=user.email,
            role_name=role.name
        )

