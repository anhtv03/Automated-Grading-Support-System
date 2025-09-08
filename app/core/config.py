import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "")
    BACKEND_URL = os.getenv("BACKEND_URL", "")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "")
    ACCESS_KEY = os.getenv("ACCESS_KEY", "")
    REFRESH_KEY = os.getenv("REFRESH_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "")
    ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "")
    REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_SECRET_KEY = os.getenv("GOOGLE_SECRET_KEY", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    API_PREFIX = ''
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "")
    MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", "")
    MEMCACHED_PORT = os.getenv("MEMCACHED_PORT", "")
    STMP_SERVER = os.getenv("STMP_SERVER", "")
    SMTP_PORT = os.getenv("SMTP_PORT", "")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
    BACKEND_CORS_ORIGINS = ['*']
    LOGGING_CONFIG_FILE = os.path.join(BASE_DIR, 'logging.ini')
    COPYLEAKS_EMAIL = os.getenv("COPYLEAKS_EMAIL", "")
    COPYLEAKS_API_KEY = os.getenv("COPYLEAKS_API_KEY", "")
    # AI API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GROK_API_KEY = os.getenv("GROK_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    # API URLs
    GROK_BASE_URL = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    # Default Models
    GROK_MODEL = os.getenv("GROK_MODEL", "grok-beta")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
    CHATGPT_MODEL = os.getenv("CHATGPT_MODEL", "gpt-3.5-turbo")
    # gemini api
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")
    GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "")
    EXTRACT_PDF_KEY = os.getenv("EXTRACT_PDF_KEY", "")
settings = Settings()
