import logging

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_sqlalchemy import DBSessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.api_router import router
from app.core.config import settings
from app.db.database import engine, Base
from app.exceptions.custom_exception import CustomException
from app.exceptions.exception_handler import http_exception_handler, validation_exception_handler

logging.config.fileConfig(settings.LOGGING_CONFIG_FILE, disable_existing_loggers=False)
Base.metadata.create_all(bind=engine)


def get_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url="/api/docs",
        redoc_url="/api/re-docs",
        openapi_url="/api/openapi.json"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(DBSessionMiddleware, db_url=settings.DATABASE_URL)
    app.add_middleware(SessionMiddleware, secret_key=settings.GOOGLE_SECRET_KEY)
    app.include_router(router, prefix=settings.API_PREFIX)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(CustomException, http_exception_handler)
    return app


app = get_application()

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
