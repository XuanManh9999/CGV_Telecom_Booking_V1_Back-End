from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuthRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    token: str
    expires_at: datetime
    token_type: str = "Bearer"

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
