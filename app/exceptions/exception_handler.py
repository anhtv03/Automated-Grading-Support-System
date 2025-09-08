from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.custom_exception import CustomException
from app.schemas.sche_api_response import ResponseSchemaBase, DataResponse

async def http_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.http_code,
        content=jsonable_encoder(ResponseSchemaBase().custom_response(exc.code, exc.message))
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for error in exc.errors():
        field = ".".join([str(i) for i in error['loc'][1:]])  # Bỏ phần 'body'
        errors[field] = error['msg']

    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(
            DataResponse().custom_response("400", "Invalid data", errors)
        )
    )


async def request_validation_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for error in exc.errors():
        loc = ".".join([str(i) for i in error['loc'][1:]])  # Bỏ phần 'body'
        errors[loc] = error['msg']
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(
            ResponseSchemaBase().custom_response("400", "Invalid data", errors)
        )
    )