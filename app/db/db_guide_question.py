from typing import Optional, List

from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.session import Session

from app.db.models import GradingGuideQuestion


def get_guide_questions(db: Session, guide_id: int) -> List[GradingGuideQuestion]:
    return (db.query(GradingGuideQuestion)
            .filter(GradingGuideQuestion.grading_guide_id == guide_id)
            .all())


def db_get_grading_guide_question_by_question_id(db: Session, question_id: int, grading_guide_id: int):
    return (db.query(GradingGuideQuestion)
            .filter(GradingGuideQuestion.exam_question_id == question_id,
                    GradingGuideQuestion.grading_guide_id == grading_guide_id)
            )


def db_get_grading_guide_question_by_grading_guide_id(db: Session, grading_guide_id: int):
    return db.query(GradingGuideQuestion).filter(GradingGuideQuestion.grading_guide_id == grading_guide_id)


def db_get_grading_guide_question_by_id(db: Session, search_id: int) -> Optional[GradingGuideQuestion]:
    return db.query(GradingGuideQuestion).filter(GradingGuideQuestion.id == search_id).first()


def db_get_grading_guide_question_by_ids(db: Session, ids: List[int]) -> Optional[List[GradingGuideQuestion]]:
    if not ids:
        return []
    return db.query(GradingGuideQuestion).filter(GradingGuideQuestion.id.in_(ids)).all()


def db_create_grading_guide_question(db: Session, guide_question: GradingGuideQuestion) -> Optional[
    GradingGuideQuestion]:
    try:
        db.add(guide_question)
        db.commit()
        db.refresh(guide_question)
        return guide_question
    except Exception as e:
        db.rollback()
        raise e


def db_update_grading_guide_question(db: Session, data: GradingGuideQuestion) -> Optional[GradingGuideQuestion]:
    try:
        flag_modified(data, "criteria")
        db.commit()
        db.refresh(data)
        return data
    except Exception as e:
        db.rollback()
        raise e


def db_update_grading_guide_questions(db: Session, data: List[GradingGuideQuestion]):
    try:
        db.commit()
        for item in data:
            db.refresh(item)
    except Exception as e:
        db.rollback()
        raise e


def db_delete_grading_guide_questions(db: Session, data: List[GradingGuideQuestion]):
    try:
        for item in data:
            db.delete(item)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
