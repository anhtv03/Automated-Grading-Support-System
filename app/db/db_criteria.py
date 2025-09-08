from typing import Optional, List

from sqlalchemy.orm.session import Session

from app.db.models import Criteria


def db_create_criteria(db: Session, data: Criteria) -> Optional[Criteria]:
    try:
        db.add(data)
        db.commit()
        db.refresh(data)
        return data
    except Exception as e:
        db.rollback()
        raise e


def db_get_criteria_by_grading_guide_id(db: Session, guide_id: int) -> Optional[List[Criteria]]:
    return db.query(Criteria).filter(Criteria.grading_guide_id == guide_id).all()


def find_criteria(db: Session, guide_id: int, question_number: int, name: Optional[str] = None) -> List[Criteria]:
    try:
        query = db.query(Criteria).filter(
            Criteria.grading_guide_id == guide_id,
            Criteria.question_number == question_number
        )
        if name:
            query = query.filter(Criteria.name == name)
        return query.all()
    except Exception as e:
        db.rollback()
        raise e
