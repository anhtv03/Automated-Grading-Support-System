import re
from typing import List, Any

from fastapi import Depends
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.constants.status import UploadSessionStatus
from app.db.database import get_db
from app.db.db_exam import db_get_exam_by_id
from app.db.db_exam_question import db_get_exam_question_by_id, db_update_exam_question_content, \
    db_create_exam_question, db_get_exam_questions_by_exam_id_and_question_name, db_get_exam_question_by_ids, \
    db_update_questions, \
    db_query_exam_questions_by_exam_id, db_delete_exam_questions_by_exam_id
from app.db.db_material import db_duplicate_material, db_get_material_ids_by_question_id
from app.db.models import ExamQuestion
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.external.ai_service import AI_Service
from app.schemas.sche_exam_question import ExamQuestionGenerateRequest, ExamQuestionGenerateResponse, \
    ExamQuestionRequest, \
    ExamQuestionUpdateRequest, ExamQuestionGetRequest, ExamRequestParams, \
    ExamQuestionGeneratePromptRequest
from app.schemas.sche_material import DuplicateMaterialsRequest
from app.schemas.sche_pagination_response import parse_key_to_filters


class ExamQuestionService:

    @staticmethod
    async def generate_content_question(
            request: ExamQuestionGenerateRequest,
            db: Session = Depends(get_db)
    ) -> ExamQuestionGenerateResponse:
        try:
            exam_question = db_get_exam_question_by_id(db, request.exam_question_id)
            if not exam_question:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            criteria_dict = exam_question.criteria or {}
            bloom_taxonomy_levels = (
                request.criteria.get("bloom_taxonomy_levels", [])
                if request.criteria
                else []
            )
            criteria_dict["bloom_taxonomy_levels"] = bloom_taxonomy_levels

            content = AI_Service.generate_exam_question_by_gemini(request, db)
            new_question = ExamQuestion(
                exam_id=exam_question.exam_id,
                question_name=exam_question.question_name,
                input_prompt=request.prompt,
                content=content,
                status=UploadSessionStatus.VISIBLE,
                criteria=criteria_dict,
            )
            result = db_create_exam_question(db, new_question)

            # duplicate data material
            material_ids = db_get_material_ids_by_question_id(db, exam_question.id)
            if material_ids:
                await db_duplicate_material(db, DuplicateMaterialsRequest(
                    material_ids=material_ids,
                    old_exam_question_id=exam_question.id,
                    new_exam_question_id=result.id
                ))

            return ExamQuestionGenerateResponse.model_validate(result)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def generate_suggest_prompt(
            request: ExamQuestionGenerateRequest,
            db: Session = Depends(get_db)
    ) -> Any:
        try:
            exam_question = db_get_exam_question_by_id(db, request.exam_question_id)
            if not exam_question:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            content = AI_Service.generate_suggest_question_by_gemini(request, db)

            questions: List[str] = []
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if (line.startswith('1. ')
                        or line.startswith('2. ')
                        or line.startswith('3. ')
                        or line.startswith('4. ')
                        or line.startswith('5. ')):
                    questions.append(line[3:].strip())

            criteria_dict = exam_question.criteria or {}
            criteria_dict["suggest_question"] = questions
            bloom_taxonomy_levels = (
                request.criteria.get("bloom_taxonomy_levels", [])
                if request.criteria
                else []
            )
            criteria_dict["bloom_taxonomy_levels"] = bloom_taxonomy_levels
            exam_question.criteria = criteria_dict
            exam_question.input_prompt = request.prompt
            db_update_exam_question_content(db, exam_question)

            return questions
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def generate_suggest_input(
            request: ExamQuestionGeneratePromptRequest,
            db: Session = Depends(get_db)
    ) -> Any:
        try:
            exam_question = db_get_exam_question_by_id(db, request.exam_question_id)
            if not exam_question:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            if exam_question.input_prompt is None or exam_question.input_prompt == "":
                odd_content = request.prompt
            else:
                odd_content = exam_question.input_prompt
            content = AI_Service.generate_suggest_input_by_gemini(request, db)

            new_content = f"""{odd_content}

-------------------------suggest prompt-------------------------
{content}"""
            exam_question.input_prompt = new_content
            db_update_exam_question_content(db, exam_question)

            return new_content
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_exam_questions(
            exam_id: int,
            params: ExamRequestParams,
            db: Session = Depends(get_db)
    ) -> List[ExamQuestionGenerateResponse]:
        try:
            result = []
            query = db_query_exam_questions_by_exam_id(db, exam_id)

            if params.options:
                filters = parse_key_to_filters(ExamQuestion, params.options)
                for f in filters:
                    query = query.filter(f)

            if hasattr(ExamQuestion, params.sort_by):
                direction = desc if params.order == 'desc' else asc
                query = query.order_by(direction(getattr(ExamQuestion, params.sort_by)))

            for item in query:
                result.append(ExamQuestionGenerateResponse.model_validate(item))

            return result
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_exam_question_by_name(
            question: ExamQuestionGetRequest,
            db: Session = Depends(get_db)
    ) -> List[ExamQuestionGenerateResponse]:
        try:
            result = []
            exam_questions = db_get_exam_questions_by_exam_id_and_question_name(db, question.exam_id,
                                                                                question.question_name)
            if not exam_questions:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            for item in exam_questions:
                result.append(ExamQuestionGenerateResponse.model_validate(item))

            return result
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_exam_question_by_id(
            exam_question_id: int,
            db: Session = Depends(get_db)
    ) -> ExamQuestionGenerateResponse:
        try:
            exam_question = db_get_exam_question_by_id(db, exam_question_id)
            if not exam_question:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            return ExamQuestionGenerateResponse.model_validate(exam_question)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def create_exam_question(
            exam_question: ExamQuestionRequest,
            db: Session = Depends(get_db)
    ) -> ExamQuestionGenerateResponse:
        try:
            exam = db_get_exam_by_id(db, exam_question.exam_id)
            if not exam:
                raise CustomException(ErrorCode.EXAM_NOT_FOUND)

            result = db_create_exam_question(db, ExamQuestion(
                exam_id=exam_question.exam_id,
                question_name=exam_question.question_name,
                content=None,
                status=UploadSessionStatus.VISIBLE,
                criteria=exam_question.criteria,
            ))
            return ExamQuestionGenerateResponse.model_validate(result)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def create_exam_question_by_exam_content(
            exam_id: int,
            exam_content: str,
            db: Session
    ):
        try:
            context_pattern = r"Project Context(.*?)Question 1"
            context_match = re.search(context_pattern, exam_content, re.DOTALL)
            context = context_match.group(1).strip() if context_match else ""

            question_pattern = r"Question \d+\s*(?:\([^)]+\))?:\s*[^\n]*\n(.*?)(?=(Question \d+|$\n*|\* Notes))"
            questions = re.findall(question_pattern, exam_content, re.DOTALL)

            result = [("Context", context)]
            for i, (question_content, _) in enumerate(questions, 1):
                question_name = f"Question {i}"
                result.append((question_name, question_content.strip()))

            saved_questions = []
            for question_name, question_content in result:
                exam_question = ExamQuestion(
                    exam_id=exam_id,
                    question_name=question_name,
                    content=question_content,
                    status=UploadSessionStatus.VISIBLE
                )
                saved_question = db_create_exam_question(db, exam_question)
                if saved_question:
                    saved_questions.append(saved_question)

            return saved_questions
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_exam_question(
            exam_question_id: int,
            new_exam_question: ExamQuestionUpdateRequest,
            db: Session = Depends(get_db)
    ) -> ExamQuestionGenerateResponse:
        try:
            exam_question_exited = db_get_exam_question_by_id(db, exam_question_id)
            if not exam_question_exited:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            exam_question_exited.input_prompt = new_exam_question.input_prompt
            if new_exam_question.content:
                exam_question_exited.content = new_exam_question.content

            result = db_update_exam_question_content(db, exam_question_exited)
            return ExamQuestionGenerateResponse.model_validate(result)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def hide_exam_question(
            exam_question_ids: List[int],
            db: Session = Depends(get_db)
    ) -> bool:
        try:
            exam_questions = db_get_exam_question_by_ids(db, exam_question_ids)
            if len(exam_questions) != len(exam_question_ids):
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            for exam_question in exam_questions:
                if exam_question.status == UploadSessionStatus.VISIBLE:
                    exam_question.status = UploadSessionStatus.HIDDEN

            db_update_questions(db, exam_questions)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def visible_exam_question(
            exam_question_ids: List[int],
            db: Session = Depends(get_db)
    ) -> bool:
        try:
            exam_questions = db_get_exam_question_by_ids(db, exam_question_ids)
            if len(exam_questions) != len(exam_question_ids):
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            for exam_question in exam_questions:
                if exam_question.status == UploadSessionStatus.HIDDEN:
                    exam_question.status = UploadSessionStatus.VISIBLE

            db_update_questions(db, exam_questions)
            return True
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def delete_exam_question_by_ids(
            exam_question_id: int,
            db: Session = Depends(get_db)
    ) -> int:
        try:
            exam_question = db_get_exam_question_by_id(db, exam_question_id)
            if not exam_question:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            # if exam_question.status == UploadSessionStatus.VISIBLE:
            #     raise CustomException(ErrorCode.EXAM_QUESTION_CANT_DELETE)

            count = await db_delete_exam_questions_by_exam_id(db, exam_question_id)
            return count
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
