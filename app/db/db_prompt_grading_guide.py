from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import PromptGuideQuestion
from app.schemas.sche_ai_chat import ChatMessage


def create_prompt_log(
        db: Session,
        messages: List[ChatMessage],
        response_content: str,
        grading_guide_question_id: Optional[int],
        provider: str,
        model: str
) -> Optional[int]:
    if grading_guide_question_id is None:
        return None

    try:
        # Lưu ý: Điều này yêu cầu ChatMessage phải có trường 'role'
        input_prompt = "\n".join(
            f"[{msg.role}]: {msg.content}" for msg in messages
        )

        # Tạo một bản ghi log mới
        # Lưu ý: Bạn cần đảm bảo model PromptGradingGuide có các trường
        # session_id, input_prompt, output_prompt, provider, model
        prompt_log = PromptGuideQuestion(
            grading_guide_question_id=grading_guide_question_id,
            input_prompt=input_prompt.strip(),
            output_prompt=response_content,
            provider=provider,
            model=model
        )

        db.add(prompt_log)
        db.commit()
        db.refresh(prompt_log)

        return prompt_log.id
    except Exception as e:
        db.rollback()
        return None


def create_prompt_guide(db: Session, prompt: PromptGuideQuestion) -> Optional[PromptGuideQuestion]:
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

def get_best_prompt_by_guide_id(db: Session, guide_id: int) -> Optional[PromptGuideQuestion]:
    return db.query(PromptGuideQuestion).filter(PromptGuideQuestion.grading_guide_question_id == guide_id).order_by(PromptGuideQuestion.score.desc()).first()
