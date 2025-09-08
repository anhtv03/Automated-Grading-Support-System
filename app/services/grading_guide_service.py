import asyncio
import json
import re
from typing import List, Any

from sqlalchemy.orm import Session

from app.constants.status import UploadSessionStatus, SemesterStatus
from app.db import db_grading_guide
from app.db.db_criteria import db_create_criteria
from app.db.db_exam_question import db_get_exam_question_by_id
from app.db.db_grading_guide import get_grading_guide_by_id, db_get_grading_guide_by_session_id, \
    get_grading_guide_by_name
from app.db.db_guide_question import db_get_grading_guide_question_by_id, db_create_grading_guide_question, \
    db_update_grading_guide_question
from app.db.db_prompt_grading_guide import create_prompt_guide, get_best_prompt_by_guide_id
from app.db.models import GradingGuide, GradingGuideQuestion, Criteria, PromptGuideQuestion
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.external.ai_service import AI_Service
from app.schemas.sche_grading_guide import GradingGuideRequest, GradingGuideResponse, GradingGuideCriteriaResponse, \
    GradingGuideUpdateRequest, GradingGuideGenerateRequest, GradingGuideSuggestResponse, \
    GradingGuideGeneratePromptRequest, GradingGuideGenerateQuestionRequest
from app.schemas.sche_grading_guide_question import GradingGuideQuestionResponse
from app.schemas.sche_pagination_response import PaginationCustomParams, paginate_advanced


class GradingGuideService:

    @staticmethod
    def extract_grading_guide_criteria(db: Session, content: str, grading_guide_id: int) -> List[
        GradingGuideCriteriaResponse]:
        try:
            question_pattern = r"Question (\d+)\s*(?:\([^)]+\))?:\s*(.*?)(?=(?:Question \d+|$\n*))"
            # question_pattern = r"Question (\d+)(?:\s*\([^)]+\))?\s*:(.*?)(?=(?:Question \d+|$))"
            question_matches = re.findall(question_pattern, content, re.DOTALL)

            results = []
            for question_num, question_content in question_matches:
                question_name = f"Question {question_num}"
                new_guide_question = GradingGuideQuestion(
                    grading_guide_id=grading_guide_id,
                    question_name=question_name,
                    content=question_content.strip(),
                    status=UploadSessionStatus.VISIBLE,
                )
                db_create_grading_guide_question(db, new_guide_question)

                detailed_answer_pattern = r"Detailed Answer:\s*(.*?)(?=(?:Marking Criteria|Question \d+|$\n*))"
                detailed_answer_match = re.search(detailed_answer_pattern, question_content, re.DOTALL)
                if detailed_answer_match:
                    criteria_block = detailed_answer_match.group(1)
                    criteria_matches = re.findall(r'(.+?)\s*\((\d*\.?\d* point[s]?)\)(?::|$|\n)', criteria_block)
                    for criterion, max_score in criteria_matches:
                        if criterion and max_score:
                            new_criteria = Criteria(
                                grading_guide_id=grading_guide_id,
                                name=criterion.strip(),
                                max_point=float(max_score.split()[0]),
                                question_number=int(question_num)
                            )
                            data = db_create_criteria(db, new_criteria)
                            results.append(GradingGuideCriteriaResponse.model_validate(data))

            return results
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_grading_guide_by_session_id(
            db: Session,
            params: PaginationCustomParams,
            session_id: int
    ):
        try:
            query = db_get_grading_guide_by_session_id(db, session_id)
            if params.keyword:
                query = query.filter(GradingGuide.name.ilike(f"%{params.keyword}%"))

            return paginate_advanced(model=GradingGuide, query=query, params=params)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def create_grading_guide(
            guide: GradingGuideRequest,
            db: Session,
    ) -> GradingGuideResponse:
        try:
            upload_session = get_grading_guide_by_name(db, guide.name, guide.session_id, guide.type)
            if upload_session:
                raise CustomException(ErrorCode.GUIDE_NAME_EXIST)

            new_guide = GradingGuide(
                name=guide.name,
                session_id=guide.session_id,
                type=guide.type,
            )

            created_guide = await db_grading_guide.create_grading_guide(db, new_guide)
            return GradingGuideResponse.model_validate(created_guide)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    def delete_grading_guide(
            grading_guide_id: int,
            db: Session
    ) -> None:
        try:
            search_template = db_grading_guide.get_grading_guide_by_id(db, grading_guide_id)

            if not search_template:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)
            else:
                db_grading_guide.delete_grading_guide(db, search_template)
                return None
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def update_grading_guide(
            request: GradingGuideUpdateRequest,
            db: Session,
    ) -> GradingGuideResponse:
        try:
            guide_existed = get_grading_guide_by_id(db, request.id)
            if not guide_existed:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            upload_session = get_grading_guide_by_name(db, request.name, request.session_id, request.type)
            if upload_session:
                raise CustomException(ErrorCode.GUIDE_NAME_EXIST)

            guide_existed.name = request.name

            updated_guide = db_grading_guide.update_grading_guide(db, guide_existed)
            return GradingGuideResponse.model_validate(updated_guide)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def generate_content_question(
            request: GradingGuideGenerateRequest,
            db: Session
    ) -> GradingGuideQuestionResponse:
        try:
            # Fetch grading guide data
            grading_guide_data = get_grading_guide_by_id(db, request.grading_guide_id)
            if not grading_guide_data:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            # Fetch exam question data
            exam_question_data = db_get_exam_question_by_id(db, request.exam_question_id)
            if not exam_question_data:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            # Prepare criteria and Bloom levels
            criteria_config = request.criteria or {}
            bloom_levels = criteria_config.get("bloom_taxonomy_levels", []) if criteria_config else []
            criteria_config["bloom_taxonomy_levels"] = bloom_levels

            # Generate content from multiple AI models
            generated_contents = await AI_Service.generate_by_multi_models(request, db)
            new_guide_question = GradingGuideQuestion(
                grading_guide_id=grading_guide_data.id,
                exam_question_id=exam_question_data.id,
                question_name=exam_question_data.question_name,
                input_prompt=request.prompt,
                content=generated_contents,
                status=UploadSessionStatus.VISIBLE,
                criteria=criteria_config,
            )

            result = db_create_grading_guide_question(db, new_guide_question)

            # result.content = await GradingGuideService.choose_best_guide(db, generated_contents, result)
            # db_update_grading_guide_question(db, result)

            return GradingGuideQuestionResponse.model_validate(result)
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    async def choose_best_guide(
            db: Session,
            generated_contents: dict,
            guide_question: GradingGuideQuestion
    ) -> str:
        try:
            # Define evaluation prompt
            prompt_system = (
                "You are an evaluator of grading guides for exam questions.\n"
                "Task:\n1. Read the provided grading guide (in HTML format).\n"
                "2. Evaluate it on these criteria, each scored from 0 to 5 points (integers only):\n"
                "   - Clarity: Is the guide easy to read and understand?\n"
                "   - Coverage: Does it fully address all parts of the question and project context?\n"
                "   - Fairness: Are the scoring rules unbiased and consistent?\n"
                "   - Feasibility: Can the guide realistically be applied by an automated or human grader?\n"
                "3. Compute the total_score as the sum of the four criteria (max 20).\n"
                "Output Rules:\n- Return ONLY a single valid JSON object.\n"
                "- Keys: \"clarity\", \"coverage\", \"fairness\", \"feasibility\", \"total_score\".\n"
                "- No explanation, no extra text, no formatting outside the JSON.\n"
                "Example output:\n{\"clarity\":4, \"coverage\":5, \"fairness\":4, \"feasibility\":5, \"total_score\":18}"
            )

            # Asynchronous evaluation of all contents
            async def evaluate_content(content: str, model_name: str) -> tuple:
                cleaned_content = AI_Service.remove_html_tags(content)

                if cleaned_content is None or cleaned_content.strip() == "":
                    return model_name, 0, content

                prompt_user = f"Now evaluate the following grading guide:\n{cleaned_content}"
                evaluation = await AI_Service.generate_by_gemini_async("gemini-2.5-flash", prompt_system, prompt_user)
                try:
                    evaluation = evaluation.strip()
                    if evaluation.startswith('{') and evaluation.endswith('}'):
                        eval_data = json.loads(evaluation)
                        total_score = eval_data.get("total_score", 0)
                        return model_name, total_score, content
                except json.JSONDecodeError:
                    return model_name, 0, content
                return model_name, 0, content

            # Run evaluations concurrently
            tasks = [evaluate_content(content, model_name) for model_name, content in generated_contents.items()]
            results = await asyncio.gather(*tasks)

            # Select best content and save prompts
            best_score = -1
            best_content = ""
            for model_name, total_score, content in results:
                prompt_question = PromptGuideQuestion(
                    provider=model_name,
                    model=model_name,
                    output_prompt=content,
                    status=SemesterStatus.VISIBLE,
                    grading_guide_question_id=guide_question.id,
                    score=total_score
                )
                create_prompt_guide(db, prompt_question)
                if total_score > best_score:
                    best_score = total_score
                    best_content = content

        except Exception as e:
            # Fallback to best existing prompt if error occurs
            best_prompt = get_best_prompt_by_guide_id(db, guide_question.id)
            best_content = best_prompt.output_prompt if best_prompt else ""

        return best_content


    @staticmethod
    def generate_suggest_question(
            request: GradingGuideGenerateQuestionRequest,
            db: Session
    ) -> Any:
        try:
            grading_guide = get_grading_guide_by_id(db, request.grading_guide_id)
            if not grading_guide:
                raise CustomException(ErrorCode.GUIDE_GRADING_GUIDE_NOT_FOUND)

            exam_question = db_get_exam_question_by_id(db, request.exam_question_id)
            if not exam_question:
                raise CustomException(ErrorCode.EXAM_QUESTION_NOT_FOUND)

            content = AI_Service.generate_suggest_question_grading_guide_by_gemini(request)

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

            criteria_dict = request.criteria or {}
            criteria_dict["suggest_question"] = questions
            bloom_taxonomy_levels = (
                request.criteria.get("bloom_taxonomy_levels", [])
                if request.criteria
                else []
            )
            criteria_dict["bloom_taxonomy_levels"] = bloom_taxonomy_levels

            if request.grading_guide_question_id:
                grading_guide_question = db_get_grading_guide_question_by_id(db, request.grading_guide_question_id)
                if not grading_guide_question:
                    raise CustomException(ErrorCode.GUIDE_QUESTION_NOT_FOUND)

                grading_guide_question.input_prompt = request.prompt
                grading_guide_question.criteria = criteria_dict
                db_update_grading_guide_question(db, grading_guide_question)

            else:
                new_guide_question = GradingGuideQuestion(
                    grading_guide_id=grading_guide.id,
                    exam_question_id=exam_question.id,
                    question_name=exam_question.question_name,
                    input_prompt=request.prompt,
                    status=UploadSessionStatus.VISIBLE,
                    criteria=criteria_dict,
                )
                db_create_grading_guide_question(db, new_guide_question)

            return questions
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    @staticmethod
    def generate_suggest_input(
            request: GradingGuideGeneratePromptRequest,
            db: Session
    ) -> Any:
        try:
            grading_guide_question = db_get_grading_guide_question_by_id(db, request.guide_question_id)
            if not grading_guide_question:
                raise CustomException(ErrorCode.GUIDE_QUESTION_NOT_FOUND)

            if grading_guide_question.input_prompt is None or grading_guide_question.input_prompt == "":
                odd_content = request.prompt
            else:
                odd_content = grading_guide_question.input_prompt
            content = AI_Service.generate_suggest_input_grading_guide_by_gemini(request)

            new_prompt = ""
            questions: List[str] = []
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('NewPrompt:'):
                    new_prompt = line[len('NewPrompt: '):].strip()
                elif (line.startswith('1. ')
                      or line.startswith('2. ')
                      or line.startswith('3. ')
                      or line.startswith('4. ')
                      or line.startswith('5. ')):
                    questions.append(line[3:].strip())

            new_content = f"""{odd_content}

-------------------------suggest prompt-------------------------
{new_prompt}"""

            criteria_dict = grading_guide_question.criteria or {}
            criteria_dict["suggest_question"] = questions
            bloom_taxonomy_levels = (
                request.criteria.get("bloom_taxonomy_levels", [])
                if request.criteria
                else []
            )
            criteria_dict["bloom_taxonomy_levels"] = bloom_taxonomy_levels

            # new_guide_question = GradingGuideQuestion(
            #     grading_guide_id=grading_guide_question.grading_guide_id,
            #     exam_question_id=grading_guide_question.exam_question_id,
            #     question_name=grading_guide_question.question_name,
            #     input_prompt=new_content,
            #     content=grading_guide_question.content,
            #     status=UploadSessionStatus.VISIBLE,
            #     criteria=criteria_dict,
            # )
            # db_create_grading_guide_question(db, new_guide_question)

            grading_guide_question.input_prompt = new_content
            grading_guide_question.criteria = criteria_dict
            db_update_grading_guide_question(db, grading_guide_question)

            return GradingGuideSuggestResponse(
                input_suggest=new_content,
                question_suggest=questions
            )
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
