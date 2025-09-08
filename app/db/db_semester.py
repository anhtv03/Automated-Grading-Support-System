from typing import Optional, List

from sqlalchemy.orm.session import Session

from app.db.models import Semester


def get_semesters(db: Session, user_id: int):
    return db.query(Semester).filter(Semester.user_id == user_id)


def create_semester(db: Session, semester: Semester):
    try:
        db.add(semester)
        db.commit()
        db.refresh(semester)
        return semester
    except Exception as e:
        db.rollback()
        raise e


def get_semester_by_user_id(db: Session, id: int, user_id: int) -> Optional[Semester]:
    return db.query(Semester).filter(Semester.id == id, Semester.user_id == user_id).first()


def get_semester_by_id(db: Session, id: int) -> Optional[Semester]:
    return db.query(Semester).filter(Semester.id == id).first()


def get_semester_by_name(db: Session, name: str, user_id: int, type: str) -> Optional[Semester]:
    return db.query(Semester).filter(Semester.name == name,
                                     Semester.user_id == user_id,
                                     Semester.type == type).first()


def delete_semester(db: Session, data: Semester) -> None:
    try:
        db.delete(data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


def update_semester_info(db: Session, semester: Semester):
    try:
        db.commit()
        db.refresh(semester)
    except Exception as e:
        db.rollback()
        raise e


def get_semesters_by_semester_ids(db: Session, semester_ids: List[int], user_id: int) -> List[Semester]:
    if not semester_ids:
        return []
    return db.query(Semester).filter(Semester.id.in_(semester_ids), Semester.user_id == user_id).all()


def save_semesters(db: Session, semesters: List[Semester]):
    try:
        db.commit()
        for semester in semesters:
            db.refresh(semester)
    except Exception as e:
        db.rollback()
        raise e


def delete_semesters(db: Session, semesters: List[Semester]):
    try:
        for semester in semesters:
            db.delete(semester)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
