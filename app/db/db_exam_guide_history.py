from typing import Optional

from sqlalchemy.orm.session import Session

from app.db.models import ExamGuideHistory


def db_get_guide_exam_data(db: Session, guide_id: int, exam_id: int) -> Optional[ExamGuideHistory]:
    return db.query(ExamGuideHistory).filter(ExamGuideHistory.exam_id == exam_id
                                             and ExamGuideHistory.grading_guide_id == guide_id).first()


def db_create_exam_guide_history(db: Session, data: ExamGuideHistory) -> Optional[ExamGuideHistory]:
    try:
        db.add(data)
        db.commit()
        db.refresh(data)
        return data
    except Exception as e:
        db.rollback()
        raise e


def db_delete_exam_data(db: Session, data: ExamGuideHistory) -> None:
    try:
        db.delete(data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
