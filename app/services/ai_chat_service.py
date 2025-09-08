from typing import List, Dict, Optional

import anthropic
import google.generativeai as genai
import openai
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.db_prompt_grading_guide import create_prompt_log
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.schemas.sche_ai_chat import ChatMessage, ChatResponse, AIProvider
from app.utils.http_client import http_client


class GrokService:
    @staticmethod
    def get_provider_name() -> str:
        return "grok"

    @staticmethod
    async def chat_completion(
            messages: List[ChatMessage],
            max_tokens: int,
            temperature: float,
            model: Optional[str] = None,
            grading_guide_question_id: Optional[int] = None,
            db: Session = Depends(get_db)
    ) -> ChatResponse:
        try:
            if not settings.GROK_API_KEY:
                raise CustomException(ErrorCode.AI_API_KEY_MISSING)

            selected_model = model or settings.GROK_MODEL
            headers = {
                "Authorization": f"Bearer {settings.GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": selected_model,
                "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            response_data = await http_client.post(
                f"{settings.GROK_BASE_URL}/chat/completions",
                headers=headers,
                json_data=payload
            )

            content = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage")
            prompt_log_id = create_prompt_log(db, messages, content, grading_guide_question_id, "grok", selected_model)

            return ChatResponse(
                provider="grok",
                model=selected_model,
                content=content,
                usage=usage,
                success=True,
                error=None,
                prompt_log_id=prompt_log_id
            )
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.AI_REQUEST_FAILED)

    @staticmethod
    async def health_check(db: Session = Depends(get_db)) -> bool:
        try:
            test_messages = [ChatMessage(role="user", content="Hello")]
            response = await GrokService.chat_completion(
                messages=test_messages,
                max_tokens=10,
                temperature=0.7,
                model=None,
                grading_guide_question_id=None,
                db=db
            )
            return response.success
        except Exception:
            return False


class DeepseekService:
    @staticmethod
    def get_provider_name() -> str:
        return "deepseek"

    @staticmethod
    async def chat_completion(
            messages: List[ChatMessage],
            max_tokens: int,
            temperature: float,
            model: Optional[str] = None,
            grading_guide_question_id: Optional[int] = None,
            db: Session = Depends(get_db)
    ) -> ChatResponse:
        try:
            if not settings.DEEPSEEK_API_KEY:
                raise CustomException(ErrorCode.AI_API_KEY_MISSING)

            selected_model = model or settings.DEEPSEEK_MODEL
            headers = {
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": selected_model,
                "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            response_data = await http_client.post(
                f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
                headers=headers,
                json_data=payload
            )

            content = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage")
            prompt_log_id = create_prompt_log(db, messages, content, grading_guide_question_id, "deepseek",
                                              selected_model)

            return ChatResponse(
                provider="deepseek",
                model=selected_model,
                content=content,
                usage=usage,
                success=True,
                error=None,
                prompt_log_id=prompt_log_id
            )
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.AI_REQUEST_FAILED)

    @staticmethod
    async def health_check(db: Session = Depends(get_db)) -> bool:
        try:
            test_messages = [ChatMessage(role="user", content="Hello")]
            response = await DeepseekService.chat_completion(
                messages=test_messages,
                max_tokens=10,
                temperature=0.7,
                model=None,
                grading_guide_question_id=None,
                db=db
            )
            return response.success
        except Exception:
            return False


class ClaudeService:
    @staticmethod
    def get_provider_name() -> str:
        return "claude"

    @staticmethod
    async def chat_completion(
            messages: List[ChatMessage],
            max_tokens: int,
            temperature: float,
            model: Optional[str] = None,
            grading_guide_question_id: Optional[int] = None,
            db: Session = Depends(get_db)
    ) -> ChatResponse:
        try:
            if not settings.ANTHROPIC_API_KEY:
                raise CustomException(ErrorCode.AI_API_KEY_MISSING)

            selected_model = model or settings.CLAUDE_MODEL
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

            system_message = ""
            claude_messages = []
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    claude_messages.append({"role": msg.role, "content": msg.content})

            kwargs = {
                "model": selected_model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": claude_messages
            }
            if system_message:
                kwargs["system"] = system_message

            response = await client.messages.create(**kwargs)

            content = response.content[0].text
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            prompt_log_id = create_prompt_log(db, messages, content, grading_guide_question_id, "claude",
                                              selected_model)

            return ChatResponse(
                provider="claude",
                model=selected_model,
                content=content,
                usage=usage,
                success=True,
                error=None,
                prompt_log_id=prompt_log_id
            )
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.AI_REQUEST_FAILED)

    @staticmethod
    async def health_check(db: Session = Depends(get_db)) -> bool:
        try:
            test_messages = [ChatMessage(role="user", content="Hello")]
            response = await ClaudeService.chat_completion(
                messages=test_messages,
                max_tokens=10,
                temperature=0.7,
                model=None,
                grading_guide_question_id=None,
                db=db
            )
            return response.success
        except Exception:
            return False


class GeminiService:
    @staticmethod
    def get_provider_name() -> str:
        return "gemini"

    @staticmethod
    async def chat_completion(
            messages: List[ChatMessage],
            max_tokens: int,
            temperature: float,
            model: Optional[str] = None,
            grading_guide_question_id: Optional[int] = None,
            db: Session = Depends(get_db)
    ) -> ChatResponse:
        try:
            if not settings.GEMINI_API_KEY:
                raise CustomException(ErrorCode.AI_API_KEY_MISSING)

            selected_model = model or settings.GEMINI_MODEL
            genai.configure(api_key=settings.GEMINI_API_KEY)

            client = genai.GenerativeModel(selected_model)
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            prompt = "\n\n".join(f"{msg.role.capitalize()}: {msg.content}" for msg in messages)
            response = await client.generate_content_async(
                prompt, generation_config=generation_config
            )

            content = response.text
            usage = None
            if response.usage_metadata:
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                }
            prompt_log_id = create_prompt_log(db, messages, content, grading_guide_question_id, "gemini",
                                              selected_model)

            return ChatResponse(
                provider="gemini",
                model=selected_model,
                content=content,
                usage=usage,
                success=True,
                error=None,
                prompt_log_id=prompt_log_id
            )
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.AI_REQUEST_FAILED)

    @staticmethod
    async def health_check(db: Session = Depends(get_db)) -> bool:
        try:
            test_messages = [ChatMessage(role="user", content="Hello")]
            response = await GeminiService.chat_completion(
                messages=test_messages,
                max_tokens=10,
                temperature=0.7,
                model=None,
                grading_guide_question_id=None,
                db=db
            )
            return response.success
        except Exception:
            return False


class ChatGPTService:
    @staticmethod
    def get_provider_name() -> str:
        return "chatgpt"

    @staticmethod
    async def chat_completion(
            messages: List[ChatMessage],
            max_tokens: int,
            temperature: float,
            model: Optional[str] = None,
            grading_guide_question_id: Optional[int] = None,
            db: Session = Depends(get_db)
    ) -> ChatResponse:
        try:
            if not settings.OPENAI_API_KEY:
                raise CustomException(ErrorCode.AI_API_KEY_MISSING)

            selected_model = model or settings.CHATGPT_MODEL
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            response = await client.chat.completions.create(
                model=selected_model,
                messages=[{"role": msg.role, "content": msg.content} for msg in messages],
                max_tokens=max_tokens,
                temperature=temperature
            )
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            prompt_log_id = create_prompt_log(db, messages, content, grading_guide_question_id, "chatgpt",
                                              selected_model)

            return ChatResponse(
                provider="chatgpt",
                model=selected_model,
                content=content,
                usage=usage,
                success=True,
                error=None,
                prompt_log_id=prompt_log_id
            )
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.AI_REQUEST_FAILED)

    @staticmethod
    async def health_check(db: Session = Depends(get_db)) -> bool:
        try:
            test_messages = [ChatMessage(role="user", content="Hello")]
            response = await ChatGPTService.chat_completion(
                messages=test_messages,
                max_tokens=10,
                temperature=0.7,
                model=None,
                grading_guide_question_id=None,
                db=db
            )
            return response.success
        except Exception:
            return False


class AIServiceFactory:
    @staticmethod
    def get_service(provider: AIProvider) -> type:
        service_map = {
            AIProvider.GROK: GrokService,
            AIProvider.CLAUDE: ClaudeService,
            AIProvider.DEEPSEEK: DeepseekService,
            AIProvider.GEMINI: GeminiService,
            AIProvider.CHATGPT: ChatGPTService
        }
        if provider not in service_map:
            raise CustomException(ErrorCode.AI_PROVIDER_NOT_FOUND)
        return service_map[provider]

    @staticmethod
    async def health_check_all(db: Session = Depends(get_db)) -> Dict[str, bool]:
        try:
            results = {}
            for provider in AIProvider:
                service_class = AIServiceFactory.get_service(provider)
                results[provider.value] = await service_class.health_check(db)
            return results
        except CustomException as e:
            raise
        except Exception as e:
            raise CustomException(ErrorCode.INTERNAL_SERVER_ERROR)
