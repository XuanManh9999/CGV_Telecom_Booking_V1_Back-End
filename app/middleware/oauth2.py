from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from typing import Optional
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: int = payload.get("role")
        chat_id: int = payload.get("chat_id")
        exp: datetime = payload.get("exp")

        if username is None or user_id is None:
            raise credentials_exception

        return {
            "username": username,
            "user_id": user_id,
            "role": role,
            "chat_id": chat_id
        }
    except JWTError:
        raise credentials_exception


def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Tạo decorator để kiểm tra role
def check_role(required_roles: list):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user["role"] not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action"
            )
        return current_user

    return role_checker
