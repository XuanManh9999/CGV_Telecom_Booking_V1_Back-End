from fastapi import Request, HTTPException, status
from jose import JWTError, jwt
from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
def exact_token(request: Request):
    try:
        auth_header = request.headers.get("Authorization")
        parts = auth_header.split()
        token = parts[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user_name": payload["sub"],
            "user_id": payload["user_id"],
            "role": payload["role"],
            "chat_id": payload["chat_id"],
            "exp": payload["exp"],
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )