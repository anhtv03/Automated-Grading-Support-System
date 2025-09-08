from typing import List

from pydantic import EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import Session

from app.constants.status import Status
from app.db.models import Users, Role
from app.schemas.sche_role import RoleResponse
from app.schemas.sche_user import UserRequest, UserInformation
from app.utils.password_util import hash_password, generate_random_password


def get_other_users(
        db: Session,
        user_id: int
):
    return db.query(Users).options(joinedload(Users.role)).filter(Users.id != user_id)

def get_total_element(
        db: Session,
        search_text: str = "",
        role_id: int = 0,
        status: str = None,
        admin_id: int = None
) -> List[Users]:
    # Build query with filtering and pagination
    query = db.query(Users)
    if admin_id is not None:
        query = query.filter(Users.id != admin_id)

    if search_text:
        search_lower = search_text.lower()
        query = query.filter(
            or_(
                Users.email.ilike(f"%{search_lower}%"),
                Users.full_name.ilike(f"%{search_lower}%")
            )
        )

    if status is not None:
        query = query.filter(Users.status == status)

    if role_id != 0:
        query = query.filter(Users.role_id == role_id)

    return query.all()


def get_roles(db: Session) -> List[Role]:
    return db.query(Role).all()


def get_user_by_email(db: Session, email: EmailStr) -> Users | None:
    return db.query(Users).filter(Users.email == email).first()


def update_user_password(db: Session, new_password: str, user: Users) -> bool:
    try:
        hashed_password = hash_password(new_password)
        user.password = hashed_password
        db.commit()
        db.refresh(user)
        return True
    except Exception as e:
        db.rollback()
        raise e


def get_role_by_user_id(db: Session, user_id: int) -> RoleResponse:
    return db.query(Role).join(Users, Role.id == Users.role_id).filter(Users.id == user_id).first()


def create_user_information(db: Session, user_information: UserInformation) -> str:
    try:
        random_password = generate_random_password(8)
        hashed_password = hash_password(random_password)

        user = Users(
            email=str(user_information.email),
            full_name=user_information.full_name,
            password=hashed_password,
            status=Status.ACTIVE,
            role_id=user_information.role_id
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return random_password
    except Exception as e:
        db.rollback()
        raise e


def update_user_information(db: Session, user: Users, user_updated: UserRequest) -> bool:
    try:
        user.full_name = user_updated.full_name
        db.commit()
        db.refresh(user)
        return True
    except Exception as e:
        db.rollback()
        raise e


def get_user_by_id(db: Session, user_id: int) -> Users | None:
    return db.query(Users).filter(Users.id == user_id).first()


def update_user_status(db: Session, user: Users, new_status: str) -> Users:
    try:
        user.status = new_status
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise e


def get_users_by_ids(db: Session, user_ids: List[int]) -> List[Users]:
    return db.query(Users).filter(Users.id.in_(user_ids)).all()


def delete_user(db: Session, user: Users) -> None:
    try:
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


def get_role_by_id(db: Session, role_id: int) -> Role | None:
    return db.query(Role).filter(Role.id == role_id).first()


def get_users_by_emails(db: Session, emails: List[EmailStr]) -> List[Users]:
    return db.query(Users).filter(Users.email.in_(emails)).all()


def get_status_course_leader(db: Session) -> bool | None:
    return db.query(Users).filter(Users.role_id == 3, Users.status == Status.ACTIVE).first() is not None
