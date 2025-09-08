import datetime
from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, Double, ForeignKeyConstraint, Identity, Index, Integer, \
    PrimaryKeyConstraint, Sequence, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Prompt(Base):
    __tablename__ = 'prompt'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='tbl_prompt_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    function_name: Mapped[Optional[str]] = mapped_column(String(100))
    prompt: Mapped[Optional[str]] = mapped_column(Text)


class Role(Base):
    __tablename__ = 'role'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='tbl_role_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))

    users: Mapped[List['Users']] = relationship('Users', back_populates='role', passive_deletes=True)


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE', name='fk_user_has_role'),
        PrimaryKeyConstraint('id', name='tbl_user_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    role_id: Mapped[int] = mapped_column(Integer)
    email: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(True, 6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(True, 6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))

    role: Mapped['Role'] = relationship('Role', back_populates='users')
    semester: Mapped[List['Semester']] = relationship('Semester', back_populates='user', passive_deletes=True)


class Semester(Base):
    __tablename__ = 'semester'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_user_semesters'),
        PrimaryKeyConstraint('id', name='tbl_semesters_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))
    status: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("'visible'::character varying"))
    type: Mapped[Optional[str]] = mapped_column(String(50))

    user: Mapped['Users'] = relationship('Users', back_populates='semester')
    upload_session: Mapped[List['UploadSession']] = relationship('UploadSession', back_populates='semester',
                                                                 passive_deletes=True)


class UploadSession(Base):
    __tablename__ = 'upload_session'
    __table_args__ = (
        ForeignKeyConstraint(['parent_session_id'], ['upload_session.id'], ondelete='CASCADE',
                             name='fk_parent_session_upload_session'),
        ForeignKeyConstraint(['semester_id'], ['semester.id'], ondelete='CASCADE', name='fk_semester_upload_session'),
        PrimaryKeyConstraint('id', name='tbl_upload_session_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    semester_id: Mapped[Optional[int]] = mapped_column(Integer)
    parent_session_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))
    grading_status: Mapped[Optional[str]] = mapped_column(String(50))
    ai_detector_status: Mapped[Optional[str]] = mapped_column(String(50))
    plagiarism_status: Mapped[Optional[str]] = mapped_column(String(50))
    task_ai: Mapped[Optional[str]] = mapped_column(String(50))
    task_plagiarism: Mapped[Optional[str]] = mapped_column(String(50))
    task_grading: Mapped[Optional[str]] = mapped_column(String(50))

    parent_session: Mapped[Optional['UploadSession']] = relationship('UploadSession', remote_side=[id],
                                                                     back_populates='parent_session_reverse')
    parent_session_reverse: Mapped[List['UploadSession']] = relationship('UploadSession',
                                                                         remote_side=[parent_session_id],
                                                                         back_populates='parent_session',
                                                                         passive_deletes=True)
    semester: Mapped[Optional['Semester']] = relationship('Semester', back_populates='upload_session')
    answer_template: Mapped[List['AnswerTemplate']] = relationship('AnswerTemplate', back_populates='session',
                                                                   passive_deletes=True)
    exam: Mapped[List['Exam']] = relationship('Exam', back_populates='session', passive_deletes=True)
    grading_guide: Mapped[List['GradingGuide']] = relationship('GradingGuide', back_populates='session',
                                                               passive_deletes=True)
    submission: Mapped[List['Submission']] = relationship('Submission', back_populates='session', passive_deletes=True)


class AnswerTemplate(Base):
    __tablename__ = 'answer_template'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['upload_session.id'], ondelete='CASCADE',
                             name='fk_session_upload_answer_template'),
        PrimaryKeyConstraint('id', name='tbl_answer_template_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    session_id: Mapped[int] = mapped_column(Integer)
    file_key: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))
    question_number: Mapped[Optional[int]] = mapped_column(Integer)

    session: Mapped['UploadSession'] = relationship('UploadSession', back_populates='answer_template')


class Exam(Base):
    __tablename__ = 'exam'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['upload_session.id'], ondelete='CASCADE', name='fk_session_upload_exam'),
        PrimaryKeyConstraint('id', name='exam_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    file_key: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))

    session: Mapped[Optional['UploadSession']] = relationship('UploadSession', back_populates='exam')
    exam_guide_history: Mapped[List['ExamGuideHistory']] = relationship('ExamGuideHistory', back_populates='exam',
                                                                        passive_deletes=True)
    exam_question: Mapped[List['ExamQuestion']] = relationship('ExamQuestion', back_populates='exam',
                                                               passive_deletes=True)


class GradingGuide(Base):
    __tablename__ = 'grading_guide'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['upload_session.id'], ondelete='CASCADE',
                             name='fk_session_upload_grading_guide'),
        PrimaryKeyConstraint('id', name='tbl_grading_guide_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    session_id: Mapped[int] = mapped_column(Integer)
    file_key: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))
    question_number: Mapped[Optional[int]] = mapped_column(Integer)

    session: Mapped['UploadSession'] = relationship('UploadSession', back_populates='grading_guide')
    criteria: Mapped[List['Criteria']] = relationship('Criteria', back_populates='grading_guide', passive_deletes=True)
    exam_guide_history: Mapped[List['ExamGuideHistory']] = relationship('ExamGuideHistory',
                                                                        back_populates='grading_guide',
                                                                        passive_deletes=True)
    grading_guide_question: Mapped[List['GradingGuideQuestion']] = relationship('GradingGuideQuestion',
                                                                                back_populates='grading_guide',
                                                                                passive_deletes=True)


class Submission(Base):
    __tablename__ = 'submission'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['upload_session.id'], ondelete='CASCADE',
                             name='fk_session_upload_submission'),
        PrimaryKeyConstraint('id', name='tbl_submission_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    session_id: Mapped[int] = mapped_column(Integer)
    file_key: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(String(50))
    final_score: Mapped[Optional[float]] = mapped_column(Double(53))
    has_ai_plagiarism: Mapped[Optional[bool]] = mapped_column(Boolean)
    ai_plagiarism_score: Mapped[Optional[float]] = mapped_column(Double(53))

    session: Mapped['UploadSession'] = relationship('UploadSession', back_populates='submission')
    submission_question: Mapped[List['SubmissionQuestion']] = relationship('SubmissionQuestion',
                                                                           back_populates='submission',
                                                                           passive_deletes=True)


class Criteria(Base):
    __tablename__ = 'criteria'
    __table_args__ = (
        ForeignKeyConstraint(['grading_guide_id'], ['grading_guide.id'], ondelete='CASCADE',
                             name='fk_criteria_grading_guide'),
        PrimaryKeyConstraint('id', name='question_criteria_pkey'),
        Index('fki_fk_criteria_grading_guide', 'grading_guide_id')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    grading_guide_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    max_point: Mapped[Optional[float]] = mapped_column(Double(53))
    question_number: Mapped[Optional[int]] = mapped_column(Integer)
    grading_guide_question_id: Mapped[Optional[int]] = mapped_column(Integer)

    grading_guide: Mapped['GradingGuide'] = relationship('GradingGuide', back_populates='criteria')
    score_history: Mapped[List['ScoreHistory']] = relationship('ScoreHistory', back_populates='criteria',
                                                               passive_deletes=True)


class ExamGuideHistory(Base):
    __tablename__ = 'exam_guide_history'
    __table_args__ = (
        ForeignKeyConstraint(['exam_id'], ['exam.id'], ondelete='CASCADE', name='fk_exam_guide_history_exam'),
        ForeignKeyConstraint(['grading_guide_id'], ['grading_guide.id'], ondelete='CASCADE',
                             name='fk_exam_guide_history_grading_guide'),
        PrimaryKeyConstraint('exam_id', 'grading_guide_id', name='exam_guide_history_pkey')
    )

    exam_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grading_guide_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))

    exam: Mapped['Exam'] = relationship('Exam', back_populates='exam_guide_history')
    grading_guide: Mapped['GradingGuide'] = relationship('GradingGuide', back_populates='exam_guide_history')


class ExamQuestion(Base):
    __tablename__ = 'exam_question'
    __table_args__ = (
        ForeignKeyConstraint(['exam_id'], ['exam.id'], ondelete='CASCADE', name='fk_exam_question_exam'),
        PrimaryKeyConstraint('id', name='exam_question_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    exam_id: Mapped[int] = mapped_column(Integer)
    question_name: Mapped[str] = mapped_column(String(50))
    input_prompt: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(True, 6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))
    criteria: Mapped[Optional[dict]] = mapped_column(JSONB)

    exam: Mapped['Exam'] = relationship('Exam', back_populates='exam_question')
    grading_guide_question: Mapped[List['GradingGuideQuestion']] = relationship('GradingGuideQuestion',
                                                                                back_populates='exam_question',
                                                                                passive_deletes=True)
    material: Mapped[List['Material']] = relationship('Material', back_populates='exam_question', passive_deletes=True)


class SubmissionQuestion(Base):
    __tablename__ = 'submission_question'
    __table_args__ = (
        ForeignKeyConstraint(['submission_id'], ['submission.id'], ondelete='CASCADE',
                             name='fk_submission_of_question'),
        PrimaryKeyConstraint('id', name='tbl_question_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    submission_id: Mapped[int] = mapped_column(Integer, Sequence('question_submission_id_seq'))
    question_name: Mapped[str] = mapped_column(String(50))
    content: Mapped[Optional[str]] = mapped_column(Text)
    cluster_id: Mapped[Optional[int]] = mapped_column(SmallInteger)
    ai_comment: Mapped[Optional[str]] = mapped_column(Text)
    expert_comment: Mapped[Optional[str]] = mapped_column(Text)

    submission: Mapped['Submission'] = relationship('Submission', back_populates='submission_question')
    plagiarism_result: Mapped[List['PlagiarismResult']] = relationship('PlagiarismResult',
                                                                       foreign_keys='[PlagiarismResult.plagiarism_id]',
                                                                       back_populates='plagiarism',
                                                                       passive_deletes=True)
    plagiarism_result_: Mapped[List['PlagiarismResult']] = relationship('PlagiarismResult',
                                                                        foreign_keys='[PlagiarismResult.source_id]',
                                                                        back_populates='source', passive_deletes=True)
    score_history: Mapped[List['ScoreHistory']] = relationship('ScoreHistory', back_populates='question',
                                                               passive_deletes=True)


class GradingGuideQuestion(Base):
    __tablename__ = 'grading_guide_question'
    __table_args__ = (
        ForeignKeyConstraint(['exam_question_id'], ['exam_question.id'], ondelete='CASCADE',
                             name='fk_grading_guide_question_exam_question'),
        ForeignKeyConstraint(['grading_guide_id'], ['grading_guide.id'], ondelete='CASCADE',
                             name='fk_grading_guide_question_grading_guide'),
        PrimaryKeyConstraint('id', name='grading_guide_question_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    grading_guide_id: Mapped[int] = mapped_column(Integer)
    input_prompt: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    exam_question_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))
    criteria: Mapped[Optional[dict]] = mapped_column(JSONB)
    question_name: Mapped[Optional[str]] = mapped_column(String(50))

    exam_question: Mapped[Optional['ExamQuestion']] = relationship('ExamQuestion',
                                                                   back_populates='grading_guide_question')
    grading_guide: Mapped['GradingGuide'] = relationship('GradingGuide', back_populates='grading_guide_question')
    prompt_guide_question: Mapped[List['PromptGuideQuestion']] = relationship('PromptGuideQuestion',
                                                                              back_populates='grading_guide_question',
                                                                              passive_deletes=True)


class Material(Base):
    __tablename__ = 'material'
    __table_args__ = (
        ForeignKeyConstraint(['exam_question_id'], ['exam_question.id'], ondelete='CASCADE',
                             name='material_exam_question_id_fkey'),
        PrimaryKeyConstraint('id', name='material_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    file_key: Mapped[str] = mapped_column(String(255))
    exam_question_id: Mapped[int] = mapped_column(Integer)

    exam_question: Mapped['ExamQuestion'] = relationship('ExamQuestion', back_populates='material')


class PlagiarismResult(Base):
    __tablename__ = 'plagiarism_result'
    __table_args__ = (
        ForeignKeyConstraint(['plagiarism_id'], ['submission_question.id'], ondelete='CASCADE',
                             name='fk_plagiarism_question'),
        ForeignKeyConstraint(['source_id'], ['submission_question.id'], ondelete='CASCADE', name='fk_source_question'),
        PrimaryKeyConstraint('id', name='tbl_plagiarism_result_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer)
    plagiarism_id: Mapped[int] = mapped_column(Integer)
    similarity_score: Mapped[float] = mapped_column(Double(53))

    plagiarism: Mapped['SubmissionQuestion'] = relationship('SubmissionQuestion', foreign_keys=[plagiarism_id],
                                                            back_populates='plagiarism_result')
    source: Mapped['SubmissionQuestion'] = relationship('SubmissionQuestion', foreign_keys=[source_id],
                                                        back_populates='plagiarism_result_')


class ScoreHistory(Base):
    __tablename__ = 'score_history'
    __table_args__ = (
        CheckConstraint('ai_score IS NULL OR ai_score >= 0::double precision', name='chk_ai_score_non_negative'),
        CheckConstraint('expert_score IS NULL OR expert_score >= 0::double precision',
                        name='chk_expert_score_non_negative'),
        ForeignKeyConstraint(['criteria_id'], ['criteria.id'], ondelete='CASCADE',
                             name='criteria_history_criteria_id_fkey'),
        ForeignKeyConstraint(['question_id'], ['submission_question.id'], ondelete='CASCADE',
                             name='criteria_history_question_id_fkey'),
        PrimaryKeyConstraint('question_id', 'criteria_id', name='criteria_history_pkey')
    )

    question_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    criteria_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ai_score: Mapped[Optional[float]] = mapped_column(Double(53))
    expert_score: Mapped[Optional[float]] = mapped_column(Double(53))

    criteria: Mapped['Criteria'] = relationship('Criteria', back_populates='score_history')
    question: Mapped['SubmissionQuestion'] = relationship('SubmissionQuestion', back_populates='score_history')


class PromptGuideQuestion(Base):
    __tablename__ = 'prompt_guide_question'
    __table_args__ = (
        ForeignKeyConstraint(['grading_guide_question_id'], ['grading_guide_question.id'], ondelete='SET NULL',
                             name='fk_prompt_guide_question_grading_guide_question'),
        PrimaryKeyConstraint('id', name='prompt_grading_guide_pkey')
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647,
                                             cycle=False, cache=1), primary_key=True)
    provider: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    input_prompt: Mapped[Optional[str]] = mapped_column(Text)
    output_prompt: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6),
                                                                    server_default=text('CURRENT_TIMESTAMP'))
    grading_guide_question_id: Mapped[Optional[int]] = mapped_column(Integer)
    score: Mapped[Optional[int]] = mapped_column(Integer)

    grading_guide_question: Mapped[Optional['GradingGuideQuestion']] = relationship('GradingGuideQuestion',
                                                                                    back_populates='prompt_guide_question')
