from typing import Optional, List

from sqlalchemy.orm.session import Session

from app.db.models import GradingGuide
from app.external.aws_service import S3Uploader


def get_grading_guide_by_id(db: Session, search_id: int) -> Optional[GradingGuide]:
    return db.query(GradingGuide).filter(GradingGuide.id == search_id).first()


def get_grading_guide_by_session_id(db: Session, search_id: int) -> Optional[GradingGuide]:
    return db.query(GradingGuide).filter(GradingGuide.session_id == search_id).first()


def get_all_grading_guide_by_session_id(db: Session, search_id: int) -> Optional[GradingGuide]:
    try:
        return db.query(GradingGuide).filter(GradingGuide.session_id == search_id).all()
    except Exception as e:
        db.rollback()
        raise e


def db_get_grading_guide_by_session_id(db: Session, search_id: int):
    try:
        return db.query(GradingGuide).filter(GradingGuide.session_id == search_id)
    except Exception as e:
        db.rollback()
        raise e


def get_grading_guide_by_name(db: Session, name: str, session_id: int, type: str) -> Optional[GradingGuide]:
    return (db.query(GradingGuide)
            .filter(GradingGuide.name == name,
                    GradingGuide.session_id == session_id,
                    GradingGuide.type == type).first())


async def create_grading_guide(db: Session, data: GradingGuide) -> Optional[GradingGuide]:
    try:
        db.add(data)
        db.commit()
        db.refresh(data)
        return data
    except Exception as e:
        db.rollback()
        raise e


def update_grading_guide(db: Session, data: GradingGuide) -> Optional[GradingGuide]:
    try:
        db.commit()
        db.refresh(data)
        return data
    except Exception as e:
        db.rollback()
        raise e


def delete_grading_guide(db: Session, data: GradingGuide) -> None:
    try:
        db.delete(data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


async def db_delete_grading_guides(db: Session, ids: List[int]) -> int:
    try:
        file_keys = [item.file_key for item in db.query(GradingGuide).filter(GradingGuide.id.in_(ids)).all()]

        count = db.query(GradingGuide).filter(GradingGuide.id.in_(ids)).delete(synchronize_session=False)
        db.commit()

        for key in file_keys:
            await S3Uploader.delete_s3_file(key) if key else None

        return count
    except Exception as e:
        db.rollback()
        raise e
