from pydantic import BaseModel, field_validator
from typing import Optional
from fastapi import status

# Models Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    exp: int
    jti: str
    refresh: bool = False
    user_code: str
    user_type: str

class LoginRequest(BaseModel):
    user_code: str
    password: Optional[str] = None

    @field_validator("user_code")
    @classmethod
    def normalize_user_code(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("user_code cannot be blank")
        return v

    @field_validator("password")
    @classmethod
    def normalize_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        # TKeep exact password bytes; only map truly empty string to None
        return None if v == "" else v

# API Responses Schemas
INVALID_CREDENTIALS = {status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"}}
INVALID_OR_EXPIRED_TOKEN = {status.HTTP_401_UNAUTHORIZED: {"description": "Invalid or expired token"}}