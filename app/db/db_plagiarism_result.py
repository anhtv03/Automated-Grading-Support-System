from sqlalchemy import desc
from sqlalchemy import exc
from sqlalchemy.orm import aliased
from sqlalchemy.orm.session import Session

from app.db.models import PlagiarismResult
from app.db.models import SubmissionQuestion, Submission
from app.schemas.sche_plagiarism_result import PlagiarismCreateRequest


def save_plagiarism_result(db: Session, request: PlagiarismCreateRequest):
    new_plagiarism = PlagiarismResult(
        source_id=request.source_id,
        plagiarism_id=request.plagiarism_id,
        similarity_score=request.similarity_score
    )
    try:
        db.add(new_plagiarism)
        db.commit()
        db.refresh(new_plagiarism)
        return new_plagiarism
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise e


def get_plagiarism_results_by_session(db: Session, session_id: int):
    sq1 = aliased(SubmissionQuestion)
    sq2 = aliased(SubmissionQuestion)
    sub1 = aliased(Submission)
    sub2 = aliased(Submission)

    return (
        db.query(
            sub1.name.label("source_student"),
            sub2.name.label("plagiarism_student"),
            sq1.question_name.label("question_name"),
            PlagiarismResult.similarity_score.label("similarity_score")
        )
        .join(sq1, PlagiarismResult.source_id == sq1.id)
        .join(sq2, PlagiarismResult.plagiarism_id == sq2.id)
        .join(sub1, sq1.submission_id == sub1.id)
        .join(sub2, sq2.submission_id == sub2.id)
        .filter(
            (sq1.question_name == sq2.question_name) &
            (sub1.session_id == session_id) &
            (sub2.session_id == session_id)
        )
        .order_by(sq1.question_name, desc(PlagiarismResult.similarity_score))
        .all()
    )
