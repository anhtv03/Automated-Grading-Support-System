from typing import Optional, List

from sqlalchemy.orm.session import Session

from app.db.models import AnswerTemplate
from app.external.aws_service import S3Uploader


def get_answer_template_by_id(db: Session, search_id: int) -> Optional[AnswerTemplate]:
    return db.query(AnswerTemplate).filter(AnswerTemplate.id == search_id).first()


def get_all_answer_template_by_session_id(db: Session, search_id: int) -> Optional[AnswerTemplate]:
    return db.query(AnswerTemplate).filter(AnswerTemplate.session_id == search_id).first()


def get_all_answer_templates_by_session_id(db: Session, search_id: int) -> Optional[List[AnswerTemplate]]:
    return db.query(AnswerTemplate).filter(AnswerTemplate.session_id == search_id).all()


async def create_answer_template(db: Session, data: AnswerTemplate) -> Optional[AnswerTemplate]:
    try:
        db.add(data)
        db.commit()
        db.refresh(data)
        return data
    except Exception as e:
        db.rollback()
        raise e


def update_answer_template(db: Session, data: AnswerTemplate) -> AnswerTemplate:
    try:
        db.commit()
        db.refresh(data)
        return data
    except Exception as e:
        db.rollback()
        raise e


async def db_delete_exam_templates(db: Session, ids: List[int]) -> int:
    try:
        file_keys = [item.file_key for item in db.query(AnswerTemplate).filter(AnswerTemplate.id.in_(ids)).all()]

        count = db.query(AnswerTemplate).filter(AnswerTemplate.id.in_(ids)).delete(synchronize_session=False)
        db.commit()

        for key in file_keys:
            await S3Uploader.delete_s3_file(key) if key else None

        return count
    except Exception as e:
        db.rollback()
        raise e
