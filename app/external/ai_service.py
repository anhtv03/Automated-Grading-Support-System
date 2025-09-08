import asyncio
import os
import re
from typing import Any, List

import google.generativeai as genai
# import vertexai
from anthropic import Anthropic
from fastapi import Depends
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import PGVector
from langchain_community.vectorstores.pgvector import DistanceStrategy
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from openai import OpenAI
from sqlalchemy.orm import Session
from xai_sdk import Client
from xai_sdk.chat import user, system

from app.core.config import settings
from app.db.database import get_db
from app.db.db_exam import db_get_questions_existed_by_exam_id
from app.db.db_exam_question import db_get_exam_question_by_id, db_get_exam_questions_visible
from app.db.db_material import get_material_by_question_id
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_exam_question import ExamQuestionGenerateRequest, ExamQuestionGeneratePromptRequest
from app.schemas.sche_grading_guide import GradingGuideGenerateRequest, GradingGuideGeneratePromptRequest, \
    GradingGuideGenerateQuestionRequest

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "F:\\Python\\RAG_Gemini_Project\\agss-swt301-469816-c720c01a1821.json"
# vertexai.init(project=settings.GOOGLE_PROJECT_ID, location=settings.GOOGLE_LOCATION)
GOOGLE_API_KEYS = os.getenv("GOOGLE_API_KEYS", "").split(",")
GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS", "").split(",")

class AI_Service:

    # ========================Generate Exam================================
    @staticmethod
    def generate_exam_question_by_gemini(
            request: ExamQuestionGenerateRequest,
            db: Session = Depends(get_db),
            api_keys: List[str] = GOOGLE_API_KEYS
    ) -> str:
        if not api_keys:
            raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

        original_api_key = os.getenv("GOOGLE_API_KEY")

        for index, api_key in enumerate(api_keys):
            try:
                os.environ["GOOGLE_API_KEY"] = api_key

                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash")

                retrieved_docs = []
                exam_context_for_ai = ""

                exam_question = db_get_exam_question_by_id(db, request.exam_question_id)
                is_context = exam_question.question_name == "Context"

                if not is_context:
                    exam_context_exsited = db_get_questions_existed_by_exam_id(
                        db,
                        exam_question.exam_id,
                        "Context"
                    )
                    if not exam_context_exsited or not exam_context_exsited[0].content:
                        raise CustomException(ErrorCode.EXAM_CONTEXT_NOT_CREATED)
                    exam_context_for_ai = exam_context_exsited[0].content

                material = get_material_by_question_id(db, request.exam_question_id)
                if material:
                    collection_name = f"materials_collection_question_{material.exam_question_id}"
                    print(f"Initial collection name: {collection_name}")
                    vectorstore = PGVector(
                        connection_string=settings.DATABASE_URL,
                        embedding_function=embeddings,
                        collection_name=collection_name,
                        distance_strategy=DistanceStrategy.COSINE
                    )
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
                    retrieved_docs = retriever.invoke(request.prompt)
                elif not is_context:
                    raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

                if is_context:
                    prompt_template_to_use = AI_Service.CONTEXT_GEN_SYSTEM_PROMPT
                else:
                    prompt_template_to_use = AI_Service.QUESTION_GEN_SYSTEM_PROMPT

                criteria_dict = request.criteria if request.criteria is not None else {}
                bloom_levels = criteria_dict.get('bloom_taxonomy_levels', [])

                document_chain = create_stuff_documents_chain(llm, prompt_template_to_use)
                input_for_chain = {
                    "user_input": request.prompt,
                    "context": retrieved_docs,
                    "criteria": bloom_levels,
                    "exam_context_input": exam_context_for_ai
                }

                response = document_chain.invoke(input_for_chain)
                cleaned_response = re.sub(r'^```html\n|\n```$', '', response, flags=re.MULTILINE)

                if original_api_key:
                    os.environ["GOOGLE_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GOOGLE_API_KEY", None)

                return cleaned_response.strip()

            except CustomException as e:
                if original_api_key:
                    os.environ["GOOGLE_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GOOGLE_API_KEY", None)
                raise
            except Exception as e:
                print(f"Unexpected error with API key {index + 1}: {e}")
                if index == len(api_keys) - 1:
                    print("All API keys exhausted")
                    if original_api_key:
                        os.environ["GOOGLE_API_KEY"] = original_api_key
                    else:
                        os.environ.pop("GOOGLE_API_KEY", None)
                    raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
                continue

        if original_api_key:
            os.environ["GOOGLE_API_KEY"] = original_api_key
        else:
            os.environ.pop("GOOGLE_API_KEY", None)
        raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

    @staticmethod
    def generate_suggest_question_by_gemini(
            request: ExamQuestionGenerateRequest,
            db: Session = Depends(get_db),
            api_keys: List[str] = GOOGLE_API_KEYS
    ) -> str:
        if not api_keys:
            raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

        original_api_key = os.getenv("GOOGLE_API_KEY")

        for index, api_key in enumerate(api_keys):
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash")

                retrieved_docs = []
                exam_context_for_ai = ""

                exam_question = db_get_exam_question_by_id(db, request.exam_question_id)
                is_context = exam_question.question_name == "Context"

                if not is_context:
                    exam_context_exsited = db_get_questions_existed_by_exam_id(
                        db,
                        exam_question.exam_id,
                        "Context"
                    )
                    if not exam_context_exsited or not exam_context_exsited[0].content:
                        raise CustomException(ErrorCode.EXAM_CONTEXT_NOT_CREATED)
                    exam_context_for_ai = exam_context_exsited[0].content

                # prioritize search material
                material = get_material_by_question_id(db, request.exam_question_id)
                if material:
                    collection_name = f"materials_collection_question_{material.exam_question_id}"
                    print(f"Initial collection name: {collection_name}")
                    vectorstore = PGVector(
                        connection_string=settings.DATABASE_URL,
                        embedding_function=embeddings,
                        collection_name=collection_name,
                        distance_strategy=DistanceStrategy.COSINE
                    )
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
                    retrieved_docs = retriever.invoke(request.prompt)
                elif not is_context:
                    raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

                criteria_dict = request.criteria if request.criteria is not None else {}
                bloom_levels = criteria_dict.get('bloom_taxonomy_levels', [])

                prompt_template_to_use = AI_Service.SUGGEST_QUESTION_GEN_SYSTEM_PROMPT
                document_chain = create_stuff_documents_chain(llm, prompt_template_to_use)
                input_for_chain = {
                    "user_prompt": request.prompt,
                    "context": retrieved_docs,
                    "blooms_criteria": bloom_levels,
                    "exam_context": exam_context_for_ai
                }

                response = document_chain.invoke(input_for_chain)
                cleaned_response = re.sub(r'^```html\n|\n```$', '', response, flags=re.MULTILINE)
                cleaned_response = re.sub(r'[\\/#]', '', cleaned_response)
                cleaned_response = cleaned_response.replace('"', "'")

                if original_api_key:
                    os.environ["GOOGLE_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GOOGLE_API_KEY", None)

                return cleaned_response.strip()

            except CustomException as e:
                if original_api_key:
                    os.environ["GOOGLE_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GOOGLE_API_KEY", None)
                raise
            except Exception as e:
                print(f"Unexpected error with API key {index + 1}: {e}")
                if index == len(api_keys) - 1:
                    print("All API keys exhausted")
                    if original_api_key:
                        os.environ["GOOGLE_API_KEY"] = original_api_key
                    else:
                        os.environ.pop("GOOGLE_API_KEY", None)
                    raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
                continue

        if original_api_key:
            os.environ["GOOGLE_API_KEY"] = original_api_key
        else:
            os.environ.pop("GOOGLE_API_KEY", None)
        raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

    @staticmethod
    def generate_suggest_input_by_gemini(
            request: ExamQuestionGeneratePromptRequest,
            db: Session = Depends(get_db),
            api_keys: List[str] = GOOGLE_API_KEYS
    ) -> str:
        if not api_keys:
            raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

        original_api_key = os.getenv("GOOGLE_API_KEY")

        for index, api_key in enumerate(api_keys):
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash")

                retrieved_docs = []
                exam_context_for_ai = ""

                exam_question = db_get_exam_question_by_id(db, request.exam_question_id)
                is_context = exam_question.question_name == "Context"

                if not is_context:
                    exam_context_exsited = db_get_questions_existed_by_exam_id(
                        db,
                        exam_question.exam_id,
                        "Context"
                    )
                    if not exam_context_exsited or not exam_context_exsited[0].content:
                        raise CustomException(ErrorCode.EXAM_CONTEXT_NOT_CREATED)
                    exam_context_for_ai = exam_context_exsited[0].content

                # prioritize search material
                material = get_material_by_question_id(db, request.exam_question_id)
                if material:
                    collection_name = f"materials_collection_question_{material.exam_question_id}"
                    print(f"Initial collection name: {collection_name}")
                    vectorstore = PGVector(
                        connection_string=settings.DATABASE_URL,
                        embedding_function=embeddings,
                        collection_name=collection_name,
                        distance_strategy=DistanceStrategy.COSINE
                    )
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
                    retrieved_docs = retriever.invoke(request.prompt)
                elif not is_context:
                    raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

                criteria_dict = request.criteria if request.criteria is not None else {}
                bloom_levels = criteria_dict.get('bloom_taxonomy_levels', [])

                prompt_template_to_use = AI_Service.SUGGEST_INPUT_GEN_SYSTEM_PROMPT
                document_chain = create_stuff_documents_chain(llm, prompt_template_to_use)
                input_for_chain = {
                    "user_prompt": request.prompt,
                    "context": retrieved_docs,
                    "blooms_criteria": bloom_levels,
                    "exam_context": exam_context_for_ai,
                    "selected_questions": request.question
                }

                response = document_chain.invoke(input_for_chain)
                cleaned_response = re.sub(r'^```html\n|\n```$', '', response, flags=re.MULTILINE)
                cleaned_response = re.sub(r'[\\/#]', '', cleaned_response)
                cleaned_response = cleaned_response.replace('"', "'")

                if original_api_key:
                    os.environ["GOOGLE_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GOOGLE_API_KEY", None)

                return cleaned_response.strip()

            except CustomException as e:
                if original_api_key:
                    os.environ["GOOGLE_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GOOGLE_API_KEY", None)
                raise
            except Exception as e:
                print(f"Unexpected error with API key {index + 1}: {e}")
                if index == len(api_keys) - 1:
                    print("All API keys exhausted")
                    if original_api_key:
                        os.environ["GOOGLE_API_KEY"] = original_api_key
                    else:
                        os.environ.pop("GOOGLE_API_KEY", None)
                    raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
                continue

        if original_api_key:
            os.environ["GOOGLE_API_KEY"] = original_api_key
        else:
            os.environ.pop("GOOGLE_API_KEY", None)
        raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

    # ========================Generate Grading Guide================================
    @staticmethod
    def generate_suggest_question_grading_guide_by_gemini(
            request: GradingGuideGenerateQuestionRequest,
            api_keys: List[str] = GOOGLE_API_KEYS
    ) -> str:
        if not api_keys:
            raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

        original_api_key = os.getenv("GOOGLE_API_KEY")

        for index, api_key in enumerate(api_keys):
            try:
                llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash")

                criteria_dict = request.criteria if request.criteria is not None else {}
                bloom_levels = criteria_dict.get('bloom_taxonomy_levels', [])

                prompt_template_to_use = AI_Service.SUGGEST_QUESTION_GRADING_GUIDE_GEN_SYSTEM_PROMPT
                chain = prompt_template_to_use | llm
                input_for_chain = {
                    "user_prompt": request.prompt,
                    "blooms_criteria": bloom_levels,
                }

                response = chain.invoke(input_for_chain)
                cleaned_response = response.content if hasattr(response, 'content') else str(response)
                cleaned_response = re.sub(r'^```html\n|\n```$', '', cleaned_response, flags=re.MULTILINE)
                cleaned_response = re.sub(r'[\\/#]', '', cleaned_response)
                cleaned_response = cleaned_response.replace('"', "'")

                if original_api_key:
                    os.environ["GOOGLE_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GOOGLE_API_KEY", None)

                return cleaned_response.strip()
            except CustomException as e:
                if original_api_key:
                    os.environ["GOOGLE_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GOOGLE_API_KEY", None)
                raise
            except Exception as e:
                print(f"Unexpected error with API key {index + 1}: {e}")
                if index == len(api_keys) - 1:
                    print("All API keys exhausted")
                    if original_api_key:
                        os.environ["GOOGLE_API_KEY"] = original_api_key
                    else:
                        os.environ.pop("GOOGLE_API_KEY", None)
                    raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
                continue

        if original_api_key:
            os.environ["GOOGLE_API_KEY"] = original_api_key
        else:
            os.environ.pop("GOOGLE_API_KEY", None)
        raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

    @staticmethod
    def generate_suggest_input_grading_guide_by_gemini(
            request: GradingGuideGeneratePromptRequest,
            api_keys: List[str] = GOOGLE_API_KEYS
    ) -> str:
        if not api_keys:
            raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

        original_api_key = os.getenv("GOOGLE_API_KEY")

        for index, api_key in enumerate(api_keys):
            try:
                llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash")

                criteria_dict = request.criteria if request.criteria is not None else {}
                bloom_levels = criteria_dict.get('bloom_taxonomy_levels', [])

                prompt_template_to_use = AI_Service.SUGGEST_INPUT_GRADING_GUIDE_GEN_SYSTEM_PROMPT
                chain = prompt_template_to_use | llm
                input_for_chain = {
                    "user_prompt": request.prompt,
                    "blooms_criteria": bloom_levels,
                    "selected_questions": request.question
                }

                response = chain.invoke(input_for_chain)
                cleaned_response = response.content if hasattr(response, 'content') else str(response)
                cleaned_response = re.sub(r'^```html\n|\n```$', '', cleaned_response, flags=re.MULTILINE)
                cleaned_response = re.sub(r'[\\/#]', '', cleaned_response)
                cleaned_response = cleaned_response.replace('"', "'")
                return cleaned_response.strip()
            except CustomException as e:
                if original_api_key:
                    os.environ["GOOGLE_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GOOGLE_API_KEY", None)
                raise
            except Exception as e:
                print(f"Unexpected error with API key {index + 1}: {e}")
                if index == len(api_keys) - 1:
                    print("All API keys exhausted")
                    if original_api_key:
                        os.environ["GOOGLE_API_KEY"] = original_api_key
                    else:
                        os.environ.pop("GOOGLE_API_KEY", None)
                    raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
                continue

        if original_api_key:
            os.environ["GOOGLE_API_KEY"] = original_api_key
        else:
            os.environ.pop("GOOGLE_API_KEY", None)
        raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

    @staticmethod
    async def generate_by_gpt_async(model: str, prompt_system: str, prompt_user: str) -> str:
        client = OpenAI()
        response = await asyncio.to_thread(client.chat.completions.create,
                                           model=model,
                                           messages=[
                                               {"role": "system", "content": prompt_system},
                                               {"role": "user", "content": prompt_user}
                                           ]
                                           )
        return response.choices[0].message.content

    @staticmethod
    async def generate_by_grok_async(model: str, prompt_system: str, prompt_user: str) -> str:
        client = Client(api_key=settings.GROK_API_KEY)
        chat = client.chat.create(model=model, temperature=0)
        chat.append(system(prompt_system))
        chat.append(user(prompt_user))
        response = await asyncio.to_thread(chat.sample)
        return response.content

    @staticmethod
    async def generate_by_gemini_async(
            model: str,
            prompt_system: str,
            prompt_user: str,
            api_keys: List[str] = GEMINI_API_KEYS
    ) -> str:
        if not api_keys:
            raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

        for index, api_key in enumerate(api_keys):
            try:
                genai.configure(api_key=api_key)
                gemini_model = genai.GenerativeModel(
                    model_name=model,
                    system_instruction=prompt_system
                )

                response = await gemini_model.generate_content_async(
                    contents=prompt_user,
                )
                return response.text

            except CustomException as e:
                raise
            except Exception as e:
                print(f"Error with API key {index + 1}: {e}")
                if index == len(api_keys) - 1:
                    print("All API keys exhausted")
                    raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)
                continue

        raise CustomException(ErrorCode.COM_AI_GENERATE_FAILED)

    @staticmethod
    async def generate_by_deepseek_async(model: str, prompt_system: str, prompt_user: str) -> str:
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ]
        )
        return response.choices[0].message.content

    @staticmethod
    async def generate_by_claude_async(model: str, prompt_system: str, prompt_user: str) -> str:
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await asyncio.to_thread(
            client.messages.create,
            model=model,
            system=prompt_system,
            messages=[
                {"role": "user", "content": prompt_user}
            ],
            max_tokens=1024
        )
        return response.content[0].text

    @staticmethod
    def remove_html_tags(html_text: str) -> str:
        return re.sub('<[^>]+>', '', html_text)

    MODEL_FUNCTIONS = {
        # "gpt-5": generate_by_gpt_async,
        "gemini-2.5-flash": generate_by_gemini_async,
        # "grok-4-0709": generate_by_grok_async,
        # "deepseek-chat": generate_by_deepseek_async,
        # "claude-sonnet-4-20250514": generate_by_claude_async
    }

    @staticmethod
    async def generate_by_multi_models(
            request: GradingGuideGenerateRequest,
            db: Session
    ) -> Any:
        try:
            exam_question = db_get_exam_question_by_id(db, request.exam_question_id)
            context_of_exam = db_get_exam_questions_visible(db, exam_question.exam_id, "Context").content
            content_of_question = exam_question.content

            criteria_dict = request.criteria or {}
            bloom_levels = criteria_dict.get('bloom_taxonomy_levels', [])

            prompt_system = AI_Service.QUESTION_GRADING_GUIDE_GEN_SYSTEM_PROMPT
            prompt_user = AI_Service.remove_html_tags(AI_Service.QUESTION_GRADING_GUIDE_GEN_USER_PROMPT.format(
                user_request=request.prompt,
                project_context=context_of_exam,
                question_content=content_of_question,
                blooms_criteria=bloom_levels
            ))

            async def call_model(model_name: str) -> str:
                try:
                    result = await asyncio.wait_for(
                        AI_Service.MODEL_FUNCTIONS[model_name](model_name, prompt_system, prompt_user), timeout=60)
                    cleaned_response = result.strip()
                    cleaned_response = re.sub(r'^```html\n|\n```$', '', cleaned_response, flags=re.MULTILINE)
                    cleaned_response = cleaned_response.replace('"', "'")
                    return cleaned_response
                except asyncio.TimeoutError:
                    print(f"Timeout for {model_name}")
                    return ""
                except Exception as e:
                    print(f"Error with {model_name}: {e}")
                    return ""

            tasks = [call_model(model_name) for model_name in AI_Service.MODEL_FUNCTIONS]
            results = await asyncio.gather(*tasks)

            cleaned_results = results[0]
            cleaned_response = cleaned_results.strip()
            cleaned_response = re.sub(r'^```html\n|\n```$', '', cleaned_response, flags=re.MULTILINE)
            cleaned_response = cleaned_response.replace('"', "'")
            return cleaned_response

        except CustomException as e:
            raise
        except Exception as e:
            print(f"Error generating exam: {e}")
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)

    # ======================================Prompt template=============================================================

    # Prompt Template for Context Generation
    CONTEXT_GEN_SYSTEM_PROMPT = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert in Software testing for generating a foundational context or background for an exam. "
         "Your primary goal is to create a clear, concise, and comprehensive background that will serve as a basis for future exam questions. "
         "The generated context must be **based exclusively on the provided 'User Input', 'Retrieved Context (from book)' if available, and 'Bloom's Criteria' if provided**. "
         "Do not use any external knowledge not present in the provided contexts. "
         "\n\n"
         "**Key Instructions:**\n"
         "1.  **Format:** Your entire response MUST be **valid HTML**. Do NOT include any other text (like greetings, introductions, or conclusions) before or after the HTML block. The HTML should use only the following tags: `<div>`, `<span>`, `<p>`, `<strong>`, `<em>`, `<ul>`, `<li>`, `br`. "
         "2.  **Content:** The generated context should be comprehensive and directly verifiable from the 'User Input' or 'Retrieved Context'. If 'Bloom's Criteria' is provided and valid (e.g., Remembering, Understanding, Applying, Analyzing, Evaluating, Creating), align context with that cognitive level. If 'Bloom's Criteria' is empty or invalid, generate context without considering Bloom's Taxonomy. "
         "3.  **HTML Structure:** Ensure the HTML is well-formed. For example, wrap the entire context in a `<div>` or `<p>` tag. Use `<strong>` for important terms and `<em>` for emphasis. Utilize `<ul>` and `<li>` for lists where appropriate. "
         ),
        ("user",
         "User Input (What the user wants to cover in the context):\n{user_input}\n\n"
         "Retrieved Context (from your materials):\n{context}\n\n"
         "Bloom's Criteria (The cognitive level to target, e.g., Remembering, Understanding, Applying, Analyzing, Evaluating, Creating; optional):\n{criteria}\n\n"
         "Task: Based on the above, generate the foundational exam context.")
    ])

    # Prompt Template for Question Generation
    QUESTION_GEN_SYSTEM_PROMPT = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert in Software testing for generating exam questions for Software Testing. "
         "Your primary goal is to create a clear, concise, and open-ended question. "
         "The question must be **based exclusively on the provided 'Exam Context', 'Retrieved Context (from book)' and 'Bloom's Criteria' if provided**. "
         "Prioritize information from 'Exam Context' when available and consistent. "
         "Do not use any external knowledge not present in the provided contexts. "
         "\n\n"
         "**Key Instructions:**\n"
         "1.  **Format:** Your entire response MUST be **valid HTML**. Do NOT include any other text (like greetings, introductions, or conclusions) before or after the HTML block. The HTML should use only the following tags: `<div>`, `<span>`, `<p>`, `<strong>`, `<em>`, `<ul>`, `<li>`. "
         "2.  **Content:** The question must be clear, detailed and directly verifiable from the 'Exam Context' or 'Retrieved Context' from which to apply and give more logical questions. If 'Bloom's Criteria' is provided and valid (e.g., Remembering, Understanding, Applying, Analyzing, Evaluating, Creating), align question with that cognitive level. If 'Bloom's Criteria' is empty or invalid, generate question without considering Bloom's Taxonomy. "
         "3.  **HTML Structure:** Ensure the HTML is well-formed. For example, wrap the question in a `<p>` tag or a `<div>`. Use `<strong>` for bolding and `<em>` for italics. "
         "4.  **Context Limitations:** If the provided contexts are unclear, contain errors, or lack sufficient relevant information, respond with a simple HTML error message:\n"
         "    <p>I don't have sufficient information in the provided contexts to generate a question.</p>\n"
         "    Do NOT generate partial or incorrect HTML if the contexts are inadequate."

         "Output format:\n"
         "Structure in this order:"
         "Question ('max_score' points): 'title of question'\n"
         "'Content of question'\n"
         "Answer requirements:\n"
         "'Content of Answer requirements'"

         "Rules:"
         "- 'max_score' is the maximum score of that question, depending on the user's requirements, the score will be between 0 and 10 points."
         "- 'content of question' is the content of that question."
         "- 'content of answer requirements' is the content of Answer requirements, which will be the general requirements to answer the above question."
         ),
        ("user",
         "Exam Context (Overall background for this exam):\n{exam_context_input}\n\n"
         "Retrieved Context (from your materials):\n{context}\n\n"
         "Bloom's Criteria (The cognitive level to target, e.g., Remembering, Understanding, Applying, Analyzing, Evaluating, Creating; optional):\n{criteria}\n\n"
         "Task: Based on the above contexts, generate a question about Software Testing. The question should cover: {user_input}")
    ])

    # Prompt Template for Suggest Question Generation
    SUGGEST_QUESTION_GEN_SYSTEM_PROMPT = ChatPromptTemplate.from_messages([
        ("system",
         "You are an AI assistant for an Automated Grading Support System (AGSS) specialized in generating deeper exploration questions for Software Testing courses, "
         "aligned with Bloom's Taxonomy (levels: Remember, Understand, Apply, Analyze, Evaluate, Create). Your task is to iteratively refine the user's prompt to make it optimal for generating high-quality deeper questions focused on Software Testing topics.\n\n"

         "Process:\n"
         "1. Analyze the 'Current user prompt' and enhance it to create a new, refined prompt in English. Incorporate the 'Bloom's criteria' by ensuring the deeper questions align with the specified cognitive levels, ensuring full coverage without redundancy. If the 'Current user prompt' lacks Bloom details, explicitly add them from 'Bloom's criteria'. Focus on Software Testing context and ensure questions build upon the 'Current user prompt', 'Retrieved context', and 'Exam context'.\n\n"
         "2. Always include specifications for question format (exactly 5 questions, plain text output, numbered format with '1. ', '2. ', '3. ', '4. ', '5. ' prefixes, maximum 30 words per question) and content requirements (building upon provided 'Current user prompt', 'Retrieved context', 'Exam context' if available, aligned with 'Bloom's criteria' if specified, focused on Software Testing implications and applications, no external knowledge introduction).\n\n"
         "3. Include error handling instructions for scenarios where provided contexts or criteria are unclear, contain errors, or lack sufficient relevant information (respond with 'Error: I don't have sufficient information in the provided contexts or criteria to suggest deeper questions.').\n\n"
         "4. Format the new prompt in plain text without any markdown formatting (no # for headings, no - for lists, no ** for bold, etc.). Structure the prompt clearly using simple text formatting with line breaks and indentation where appropriate.\n\n"
         "5. Evaluate if the new prompt is optimal: clear, detailed, fully covers the provided 'Bloom's criteria' if applicable, specifies exact output format requirements, includes Software Testing context constraints, references the 'Current user prompt', 'Retrieved context', 'Exam context', and 'Bloom's criteria' appropriately, includes error handling for insufficient information, and is ready for deeper question generation without ambiguity. If yes, output \"OPTIMAL\" followed by a line break and then the refined prompt.\n\n"
         "6. If not optimal, output \"NOT OPTIMAL\" followed by a line break, then the refined prompt, then another line break, then exactly 5 new clarifying questions in English (one per line). Make them smart, open-ended, Software Testing focused, concise, and not verbose or rambling (e.g., short and practical questions like \"Focus on integration testing scenarios?\" or \"Include performance testing aspects?\").\n\n"

         "Output format:\n"
         "If optimal:\n"
         "OPTIMAL\n"
         "[refined prompt in plain text]\n\n"
         "If not optimal:\n"
         "NOT OPTIMAL\n"
         "1. [clarifying question 1]\n"
         "2. [clarifying question 2]\n"
         "3. [clarifying question 3]\n"
         "4. [clarifying question 4]\n"
         "5. [clarifying question 5]\n\n"

         "Be intelligent: Prioritize questions on Bloom level alignment from 'Bloom's criteria', exact output format specifications (plain text, exactly 5 questions, numbered format, 30-word limits), context utilization requirements ('Current user prompt', 'Retrieved context', 'Exam context', 'Bloom's criteria'), error handling for insufficient information, and Software Testing relevance. Ensure additional questions are real-world oriented, short, concise, and not rambling. Ensure the refined prompt is always in English plain text format without markdown."
         ),
        ("user",
         "Current user prompt (e.g., \"Suggest deeper questions about API testing challenges based on the provided context\". It may or may not include Bloom levels inline.): {user_prompt}\n\n"
         "Retrieved context (content from Software Testing books or materials that serves as the knowledge base for question generation if available, may be empty): {context}\n\n"
         "Exam context (specific exam or assessment context if available, may be empty): {exam_context}\n\n"
         "Bloom's criteria (specific Bloom's Taxonomy level like \"Remembering\", \"Understanding\", \"Applying\", \"Analyzing\", \"Evaluating\", \"Creating\" that should guide question alignment if available, may be empty): {blooms_criteria}\n\n"
         "Task: Based on the above contexts and Bloom's Criteria (if provided), refine the current user prompt to optimally generate exactly 5 deeper questions about Software Testing, aligned with the specified cognitive level if applicable.")
    ])

    # Prompt Template for Suggest Input Generation
    SUGGEST_INPUT_GEN_SYSTEM_PROMPT = ChatPromptTemplate.from_messages([
        ("system",
         "You are an AI assistant for an Automated Grading Support System (AGSS) specialized in generating deeper exploration questions for Software Testing courses."
         "Your task is to iteratively refine the user's prompt to make it optimal for generating high-quality deeper questions focused on Software Testing topics.\n\n"

         "Process:\n"
         "1. Analyze and  Integrate the 'Selected questions' into the 'Current user prompt' to create a new, refined prompt in English. The new prompt must address and incorporate the selected questions directly (e.g., if a selected question asks for details on tools, include them in the prompt). Incorporate the 'Bloom's criteria' by ensuring the deeper questions align with the specified cognitive levels, ensuring full coverage without redundancy. If the 'Current user prompt' lacks Bloom details, explicitly add them from 'Bloom's criteria'. Focus on Software Testing context and ensure questions build upon the 'Current user prompt', 'Retrieved context', and 'Exam context'.\n\n"
         "2. Always include considerations for the total points of the question and sub-points for each part (e.g., based on Bloom levels or complexity, such as \"Total points: 3 (0.5 for part 1, 1 for part 2, 1.5 for part 3)\"), maximum 100 words. and content requirements (building upon provided 'Current user prompt', 'Retrieved context', 'Exam context' if available, aligned with 'Bloom's criteria' if specified, focused on Software Testing implications and applications, no external knowledge introduction).\n\n"
         # "3. Include error handling instructions for scenarios where provided contexts or criteria are unclear, contain errors, or lack sufficient relevant information (respond with 'Error: I don't have sufficient information in the provided contexts or criteria to suggest deeper questions.').\n\n"
         "4. Format the new prompt in plain text without any markdown formatting (no # for headings, no - for lists, no ** for bold, etc.). Structure the prompt clearly using simple text formatting with line breaks and indentation where appropriate.\n\n"
         "5. The new prompt must be optimal: clear, detailed, fully covers the provided 'Bloom's criteria' if applicable, specifies exact output format requirements, includes Software Testing context constraints, references the 'Current user prompt', 'Retrieved context', 'Exam context', and 'Bloom's criteria' appropriately, addresses all 'Selected questions'."

         "Output Requirements:\n"
         "- Always output a single, improved prompt as a single line, maximum 100 words\n"
         "- Format in plain text without markdown\n"

         "Be intelligent: Prioritize Bloom level alignment from 'Bloom's criteria', context utilization requirements ('Current user prompt', 'Retrieved context', 'Exam context', 'Bloom's criteria'), addressing all 'Selected questions', and Software Testing relevance. Ensure the refined prompt is always in English plain text format without markdown, this refined prompt should be a question that covers all of 'Bloom's criteria', if any. . Always include considerations for the total points of the question and sub-points for each part (e.g., based on Bloom levels or complexity, such as \"Total points: 3 (0.5 for part 1, 1 for part 2, 1.5 for part 3)\"), maximum 100 words."
         ),
        ("user",
         "Current user prompt (e.g., \"Suggest deeper questions about API testing challenges based on the provided context\". It may or may not include Bloom levels inline.): {user_prompt}\n\n"
         "Retrieved context (content from Software Testing books or materials that serves as the knowledge base for question generation if available, may be empty): {context}\n\n"
         "Exam context (specific exam or assessment context if available, may be empty): {exam_context}\n\n"
         "Bloom's criteria (specific Bloom's Taxonomy level like \"Remembering\", \"Understanding\", \"Applying\", \"Analyzing\", \"Evaluating\", \"Creating\" that should guide question alignment if available, may be empty): {blooms_criteria}\n\n"
         "Selected questions (an array of 0 or more clarifying questions selected by the user, e.g., [\"Should the deeper questions focus on specific testing tools like Postman or RestAssured?\"]): {selected_questions}"
         "Task: Based on the above inputs, generate an improved version of the User Input prompt for Software Testing, incorporating insights from the Suggested Question and aligning with Bloom's Criteria if provided.")
    ])

    # Prompt Template for Suggest Generation Grading Guide
    SUGGEST_QUESTION_GRADING_GUIDE_GEN_SYSTEM_PROMPT = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert assistant for a system that generates grading guidelines for essay questions in Software Testing, aligned with the book Foundations of Software Testing ISTQB Certification by Erik van Veenendaal (2019)."
         "The user has input a prompt: 'Current user prompt' to create grading guidelines."
         "Analyze this prompt in the context of Software Testing, strictly adhering to concepts from the book (e.g., test case design, black-box testing, white-box testing, test automation, defect management, ISTQB syllabus). Incorporate the 'Bloom's criteria' by ensuring the deeper questions align with the specified cognitive levels, ensuring full coverage without redundancy."
         "Generate exactly 5 clear, concise, and relevant questions to help the user refine their prompt for better clarity and specificity. Each question must be no longer than 30 words, must focus on improving the prompt's alignment with Software Testing concepts from the book, and must avoid ambiguity (aligned with 'Bloom's criteria' if specified). "
         "You must return ONLY the result in plain text format with the exact structure numbered format with '1. ', '2. ', '3. ', '4. ', '5. ' prefixes. Do not generate any additional text, explanations, or a new prompt."

         "Output format:\n"
         "1. [clarifying question 1]\n"
         "2. [clarifying question 2]\n"
         "3. [clarifying question 3]\n"
         "4. [clarifying question 4]\n"
         "5. [clarifying question 5]\n\n"),
        ("user",
         "Current user prompt (e.g., \"Suggest deeper questions about API testing challenges based on the provided context\". It may or may not include Bloom levels inline.): {user_prompt}\n\n"
         "Bloom's criteria (specific Bloom's Taxonomy level like \"Remembering\", \"Understanding\", \"Applying\", \"Analyzing\", \"Evaluating\", \"Creating\" that should guide question alignment if available, may be empty): {blooms_criteria}\n\n"
         "Task: Based on the above inputs, Generate exactly 5 clear, concise, and relevant questions to help the user refine their prompt for better clarity and specificity. , incorporating insights from the Bloom's Criteria if provided."
         )
    ])

    # Prompt Template for Suggest input Generation Grading Guide
    SUGGEST_INPUT_GRADING_GUIDE_GEN_SYSTEM_PROMPT = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert assistant for a system that generates grading guidelines for essay questions in Software Testing, strictly aligned with the book Foundations of Software Testing ISTQB Certification by Erik van Veenendaal (2019). "
         "The user has provided an old prompt: 'Current user prompt' and optionally selected a suggestion question: 'Selected questions'. Incorporate the 'Bloom's criteria' by ensuring the deeper questions align with the specified cognitive levels, ensuring full coverage without redundancy."
         "If the  'Selected questions' is 'none', you must improve the old prompt based solely on its content to make it more optimized, ensuring alignment with Software Testing concepts from the book (e.g., test case design, black-box testing, white-box testing, test automation, defect management, ISTQB syllabus). "
         "If a 'Selected questions' is selected, you must incorporate the user's requirement from that question (e.g., adding specific details, clarifying ambiguities) into the old prompt to create an improved version that addresses the requirement and implicitly answers the question."
         "In all cases, you must generate a new, optimized prompt (100-150 words) that is clear, concise, specific, actionable, and strictly aligned with Software Testing concepts from the book. The new prompt must be suitable for generating accurate grading guidelines and avoid any irrelevant or ambiguous content."
         "Additionally, you must analyze the new prompt and generate exactly 5 new, clear, and concise questions (each under 30 words) to further refine it, focusing on potential improvements in clarity, specificity, or alignment with the book's concepts (aligned with 'Bloom's criteria' if specified)."
         "You must return ONLY the result in plain text format with the exact structure and new question numbered format with '1. ', '2. ', '3. ', '4. ', '5. ' prefixes. Do not include any additional text, explanations, or deviations from this format under any circumstances."

         "Output format:\n"
         "NewPrompt: [new prompt]\n]"
         "1. [clarifying question 1]\n"
         "2. [clarifying question 2]\n"
         "3. [clarifying question 3]\n"
         "4. [clarifying question 4]\n"
         "5. [clarifying question 5]\n\n"
         ),
        ("user",
         "Current user prompt (e.g., \"Suggest deeper questions about API testing challenges based on the provided context\". It may or may not include Bloom levels inline.): {user_prompt}\n\n"
         "Bloom's criteria (specific Bloom's Taxonomy level like \"Remembering\", \"Understanding\", \"Applying\", \"Analyzing\", \"Evaluating\", \"Creating\" that should guide question alignment if available, may be empty): {blooms_criteria}\n\n"
         "Selected questions (an array of 0 or more clarifying questions selected by the user, e.g., [\"Should the deeper questions focus on specific testing tools like Postman or RestAssured?\"]): {selected_questions}"
         "Task: Based on the above inputs, Generate a new prompt and exactly 5 clear, concise, and relevant questions to help the user refine their prompt for better clarity and specificity. , incorporating insights from the Bloom's Criteria if provided.")
    ])

    # Prompt Template for Generation Grading Guide
    QUESTION_GRADING_GUIDE_GEN_SYSTEM_PROMPT = """
You are an expert grading-guide generator for a Software Testing course (ISTQB Foundation Level, 2019 – Erik van Veenendaal).
Generate a single **HTML** grading guide for one exam question using the provided Project Context, Question Content, and Bloom’s level (Bloom is for internal guidance only; do not print it).

OUTPUT RULES
- Return ONLY HTML (no Markdown, no extra text). Allowed tags: <div>, <h3>, <p>, <ul>, <li>, <strong>, <em>, <code>, <br>.
- HTML must be valid and well-formed:
  – Every <li> MUST be closed with </li>.
  – Never output “<li><li>”. If a new item starts, previous <li> must end: “…</li><li>…”.
  – Do not nest <li> inside another <li>. For sub-details, use <p> or <br>.
  – Structure lists strictly as <ul> … <li> … </li> … </ul>. No unclosed tags.

STRUCTURE (exact order)
1) <h3><strong>Analysis</strong></h3>
   <p>1–3 sentences stating what the question assesses and which parts of the project context matter. Do NOT mention Bloom.</p>

2) <h3><strong>Detailed Answer</strong></h3>
   - Provide criteria sections as list items.
   - Each <li> begins with <strong>[Short title] (X point)</strong>:
   - Inside each <li>, after the short title, you may use either:
     - A concise <p> with 2–4 sentences, OR
     - A combination of <p> for an intro sentence + <ul> with clear bullet points for sub-items (errors, fixes, conditions).
   - Use measurable, context-specific content. Ensure clarity so the examiner can grade directly.
   - Criteria must be precise, use ISTQB terms, and reference the given project context.
   - The sum of all X must equal the question’s total points.

3) <h3><strong>Marking Criteria</strong></h3>
   <ul>
     <li>State numeric grading rules tied to Detailed Answer (full/partial/zero, explicit deductions/additions). Use thresholds, caps, and penalties where relevant. Be clear and numeric (e.g., “−0.5 points per irrelevant item, max 3 points total”).</li>
   </ul>

QUALITY REQUIREMENTS
- Detailed Answer is authoritative: it must be detailed enough for grading without further interpretation.
- Accept realistic student variations (correct, partial, incorrect, off-scope, excessive, missing).
- Balance clarity: short descriptions when sufficient, bullet points when multiple elements need separation.
- Use ISTQB terminology.
- Keep HTML clean, deterministic, and grading-oriented.

FINAL COMPLIANCE CHECK
- Output only HTML (no Markdown, no comments).
- Lists must be properly closed, no nested <li>.
- Each criterion = one <li> with short title + (X point) + body (paragraph or bullet points).
- Total points across criteria = question total.
    """

    QUESTION_GRADING_GUIDE_GEN_USER_PROMPT = """
            {user_request}
    
            Please base your grading guide on the following details:
            
            Project Context:
            {project_context}
            
            Question:
            {question_content}
            
            Bloom's Taxonomy Levels:
            {blooms_criteria}
        """
