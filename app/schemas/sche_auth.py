from pydantic import BaseModel, EmailStr, Field


class AuthBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class LoginRequest(AuthBase):
    email: EmailStr = Field(min_length=8, max_length=50)
    password: str = Field(min_length=8, max_length=50)


class LoginResponse(AuthBase):
    access_token: str
    refresh_token: str
    email: str
    role_name: str


class CodeRequest(BaseModel):
    code: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
