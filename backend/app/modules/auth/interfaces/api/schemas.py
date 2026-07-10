from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_id: str = Field(min_length=3, max_length=64)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int


class MeResponse(BaseModel):
    user_id: str
    email: str
    company_id: str
    roles: list[str]


class UserResponse(BaseModel):
    user_id: str
    email: str
    company_id: str
    roles: list[str]
