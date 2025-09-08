from enum import Enum
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class AIProvider(str, Enum):
    GROK = "grok"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    CHATGPT = "chatgpt"


class ChatMessage(BaseModel):
    role: str = Field(default="user")
    content: str = Field(default="Say Hello")


class ChatRequest(BaseModel):
    provider: AIProvider = Field(default="gemini")
    messages: List[ChatMessage] = Field(...)
    max_tokens: Optional[int] = Field(default=5)
    temperature: Optional[float] = Field(default=0.1)
    model: Optional[str] = Field(default="gemini-1.5-flash")
    grading_guide_question_id: Optional[int] = Field(default=None)


class ChatResponse(BaseModel):
    provider: str
    model: str
    content: str
    usage: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None
    prompt_log_id: Optional[int] = None  # ID của log prompt đã lưu


class HealthResponse(BaseModel):
    status: str
    providers: Dict[str, bool]


class ProviderHealthResponse(BaseModel):
    provider: str
    status: str
    healthy: bool
    error: Optional[str] = None
