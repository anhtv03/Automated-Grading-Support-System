from typing import Optional

from sqlalchemy.orm.session import Session

from app.db.models import Role


def get_role_by_id(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()
