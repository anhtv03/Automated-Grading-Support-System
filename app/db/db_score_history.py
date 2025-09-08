from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm.session import Session

from app.db.models import ScoreHistory
from app.schemas.sche_score_history import TotalScoreHistoryResponse


def get_score_history(db: Session, question_id: int, criteria_id: int) -> Optional[ScoreHistory]:
    return db.query(ScoreHistory).filter(
        ScoreHistory.question_id == question_id,
        ScoreHistory.criteria_id == criteria_id
    ).first()


def get_score_histories(db: Session, question_id: int) -> Optional[List[ScoreHistory]]:
    return db.query(ScoreHistory).filter(
        ScoreHistory.question_id == question_id
    ).all()

def db_create_score_history(db: Session, score_histories: List[ScoreHistory]):
    try:
        db.add_all(score_histories)
        db.commit()
        for score in score_histories:
            db.refresh(score)
        return score_histories
    except Exception as e:
        db.rollback()
        raise e

def db_update_score_histories(db: Session, score_history: List[ScoreHistory]):
    try:
        db.commit()
        for score in score_history:
            db.refresh(score)
    except Exception as e:
        db.rollback()
        raise e


def get_total_score_by_submission_question_id(db: Session, submission_question_id: int):
    try:
        query = """
                SELECT SUM(score_history.ai_score)     AS "AI_total_score",
                       SUM(score_history.expert_score) AS "expert_total_score"
                FROM submission_question
                         JOIN score_history ON score_history.question_id = submission_question.id
                where id = :submission_question_id
                """
        result = db.execute(text(query), {"submission_question_id": submission_question_id}).fetchone()
        return TotalScoreHistoryResponse(
            ai_total_score=result.AI_total_score,
            expert_total_score=result.expert_total_score,
        )
    except Exception as e:
        db.rollback()
        raise e
