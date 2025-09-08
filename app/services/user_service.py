import os
from datetime import datetime
from typing import Optional, List, Dict

import httpx
from fastapi import HTTPException
from pydantic import EmailStr
from pymemcache.client.base import Client
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.constants.status import Status
from app.constants.token_type import TokenType
from app.core.config import settings
from app.db import db_user
from app.db.db_role import get_role_by_id
from app.db.db_user import (get_other_users, get_user_by_email, get_users_by_ids, get_user_by_id, update_user_status,
                            create_user_information, update_user_information, get_role_by_user_id,
                            get_role_by_id, get_status_course_leader)
from app.db.models import Users, Role
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.external.email_service import send_email_smtp
from app.schemas.sche_pagination import PaginatedResponse
from app.schemas.sche_pagination_response import PaginationCustomParams, apply_in_memory_filters, \
    parse_key_to_filters_classify_email
from app.schemas.sche_role import RoleResponse
from app.schemas.sche_user import (OTPVerificationRequest, UserItemResponse,
                                   UserRequest, UserInformation,
                                   UserClassification, UserResponse,
                                   ListUserIdDelete)
from app.services.jwt_service import JwtService
from app.utils.pagination import paginate
from app.utils.security import generate_otp

memcached_client = Client((settings.MEMCACHED_HOST, settings.MEMCACHED_PORT))


class UserService:

    @staticmethod
    def get_other_users(
            db: Session,
            params: PaginationCustomParams,
            user_id: int
    ):
        try:
            query = get_other_users(db, user_id)
            if params.keyword:
                query = query.filter(
                    or_(
                        Users.full_name.ilike(f"%{params.keyword}%"),
                        Users.email.ilike(f"%{params.keyword}%")
                    )
                )
            return paginate(model=Users, query=query, params=params)

        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    # @staticmethod
    # def get_roles(db: Session):
    #     try:
    #         return get_roles(db)
    #     except CustomException as e:
    #         raise
    #     except Exception as e:
    #         raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        try:
            user = get_user_by_email(db, email)
            if not user:
                raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)
            return user
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def delete_user(db: Session, user_id: int) -> UserItemResponse:
        try:
            user_exist = get_user_by_id(db, user_id)
            if not user_exist:
                raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)

            update_user_status(db, user_exist, "deleted")
            return UserItemResponse.model_validate(user_exist)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_user_information(db: Session, id: int, user_information: UserRequest) -> UserItemResponse:
        try:
            user: Optional[Users] = get_user_by_id(db, id)
            if not user:
                raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)

            if user.email != user_information.email:
                raise CustomException(ErrorCode.AUTH_EMAIL_ALREADY_EXISTS)

            # Update user information
            isUpdate = update_user_information(db, user, user_information)

            if not isUpdate:
                raise CustomException(ErrorCode.COM_UPDATE_FAILED)
            else:
                return UserItemResponse.model_validate(user)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_role_by_user_id(db: Session, user_id: int) -> RoleResponse:
        try:
            user: Optional[Users] = get_user_by_id(db, user_id)
            if not user:
                raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)
            role = get_role_by_user_id(db, user_id)
            return RoleResponse.model_validate(role)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def create_user(db: Session, user_information: list[UserInformation]) -> bool:
        try:
            rtnCd = True

            for info in user_information:
                user: Optional[Users] = get_user_by_email(db, info.email)
                if user:
                    raise CustomException(ErrorCode.ACC_USER_ALREADY_EXISTS)

                role: Optional[Role] = get_role_by_id(db, info.role_id)
                if not role:
                    raise CustomException(ErrorCode.ACC_ROLE_NOT_FOUND)

                random_password = create_user_information(db, info)
                result = send_email_smtp(info.email, random_password, "create")
                if not result:
                    raise CustomException(ErrorCode.AUTH_EMAIL_SEND_FAILED)

            return rtnCd
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def classify_email(
            db: Session,
            params: PaginationCustomParams,
    ) -> PaginatedResponse:
        try:
            data = await UserService.fetch_api_data()
            emails = [item["email"] for item in data]

            query = db.query(Users).options(joinedload(Users.role))
            existing_users = query.filter(Users.email.in_(emails)).all()
            existing_emails = {user.email for user in existing_users}

            not_found_users = [
                UserClassification(
                    email=item["email"],
                    full_name=item.get("name", ""),
                    status="not assigned",
                    created_at=None,
                )
                for item in data
                if item["email"] not in existing_emails
            ]

            existing_user_objs = [
                UserClassification(
                    email=user.email,
                    full_name=user.full_name,
                    status=user.status,
                    created_at=user.created_at,
                )
                for user in existing_users
            ]

            all_results = not_found_users + existing_user_objs

            if params.keyword:
                all_results = [
                    result for result in all_results
                    if params.keyword.lower() in result.email.lower() or
                       params.keyword.lower() in result.full_name.lower()
                ]

            if params.options:
                filters = parse_key_to_filters_classify_email(Users, params.options)
                all_results = apply_in_memory_filters(all_results, filters)

            match params.sort_by:
                case "email":
                    all_results.sort(key=lambda x: x.email, reverse=(params.order == "desc"))
                case "full_name":
                    all_results.sort(key=lambda x: x.full_name, reverse=(params.order == "desc"))
                case "status":
                    all_results.sort(key=lambda x: x.status, reverse=(params.order == "desc"))
                case "created_at":
                    all_results.sort(key=lambda x: x.created_at or datetime.min, reverse=(params.order == "desc"))

            total = len(all_results)
            start = (params.page_no - 1) * params.page_size
            end = start + params.page_size
            paginated = all_results[start:end]

            return PaginatedResponse(
                data=paginated,
                total=total,
                page_no=params.page_no,
                page_size=params.page_size
            )

        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_users_status(db: Session, user_ids: List[int], message: str, status: str) -> int:
        try:
            users: List[Users] = get_users_by_ids(db, user_ids)
            found_ids = [user.id for user in users]
            not_found_ids = list(set(user_ids) - set(found_ids))

            if not_found_ids:
                raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)

            has_course_leader = get_status_course_leader(db)

            if status not in Status._value2member_map_:
                raise CustomException(ErrorCode.ACC_STATUS_INVALID)

            for user in users:
                if has_course_leader and user.role_id == 3:
                    raise CustomException(ErrorCode.ACC_SINGLE_ACTIVE_LEADER_VIOLATION)

                user.status = status

            for user in users:
                send_email_smtp(user.email, user.full_name+"|"+status+"|"+message,
                                "change_status")

            db.commit()
            return len(users)
        except CustomException as e:
            raise
        except Exception as e:
            print(str(e))
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_users_role(db: Session, user_ids: List[int], role_id: int) -> int:
        try:
            users: List[Users] = get_users_by_ids(db, user_ids)
            found_ids = [user.id for user in users]
            not_found_ids = list(set(user_ids) - set(found_ids))

            if not_found_ids:
                raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)

            role = get_role_by_id(db, role_id)
            for user in users:
                if user.role_id == 1 and role_id == 1:
                    raise CustomException(ErrorCode.ACC_ROLE_INVALID)

            if not role:
                raise CustomException(ErrorCode.ACC_ROLE_INVALID)

            status_course_leader = get_status_course_leader(db)
            if status_course_leader and role_id == 3:
                raise CustomException(ErrorCode.ACC_SINGLE_ACTIVE_LEADER_VIOLATION)

            if role_id == 3 and len(users) > 1:
                raise CustomException(ErrorCode.ACC_MULTIPLE_ACTIVE_LEADERS)

            for user in users:
                user.role_id = role_id

            db.commit()
            return len(users)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def fetch_api_data() -> List[Dict[str, str]]:
        url = os.getenv("API_DATA_FAP")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data: List[Dict[str, str]] = response.json()
                    print(data)
                    return data
                else:
                    print(f"Lỗi: {response.status_code}")
                    return []
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def delete_user_by_ids(db: Session, request: ListUserIdDelete) -> int:
        try:
            user_ids = request.user_ids
            users = get_users_by_ids(db, user_ids)

            if len(users) != len(user_ids):
                raise HTTPException(status_code=404, detail="Some users not found.")

            active_users = [user for user in users if user.status != 'inactive']
            if active_users:
                if active_users:
                    raise CustomException(ErrorCode.ACC_ACTIVE_CANT_DELETE)

            for user in users:
                db.delete(user)

            db.commit()
            return len(users)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def send_otp_to_update_email(db: Session, email: EmailStr) -> bool:
        try:
            user: Optional[Users] = get_user_by_email(db, email)
            if user:
                raise CustomException(ErrorCode.AUTH_EMAIL_ALREADY_EXISTS)

            if user.status != Status.ACTIVE:
                raise CustomException(ErrorCode.AUTH_INVALID_ACCOUNT_STATUS)

            otp = generate_otp()
            cache_key = F"{email}/update"

            try:
                memcached_client.set(
                    key=cache_key,
                    value=otp,
                    expire=180
                )
            except Exception as ex:
                raise CustomException(ErrorCode.AUTH_OTP_STORAGE_FAILED)

            result = send_email_smtp(email, otp, "change_email")
            if not result:
                memcached_client.delete(cache_key)
                raise CustomException(ErrorCode.AUTH_EMAIL_SEND_FAILED)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def verify_otp_to_update_email(db: Session, verify_otp_form: OTPVerificationRequest) -> bool:
        try:
            user: Optional[Users] = get_user_by_email(db, verify_otp_form.email)
            if user:
                raise CustomException(ErrorCode.AUTH_EMAIL_ALREADY_EXISTS)

            cache_key = F"{verify_otp_form.email}/update"
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
    def decode_token_user(db: Session, token: str) -> Optional[Users]:
        try:
            pay_load = JwtService.decode_jwt_token(token, TokenType.ACCESS_TOKEN)

            if not pay_load:
                return None

            user = db_user.get_user_by_id(db, pay_load["user_id"])

            if not user:
                raise CustomException(ErrorCode.ACC_USER_NOT_FOUND)

            user_respone = UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                status=user.status,
                roles=RoleResponse(id=user.role_id,
                                   name=get_role_by_id(db, user.role_id).name) if user.role_id else None
            )

            return user_respone

        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
