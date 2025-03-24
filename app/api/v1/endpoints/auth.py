from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.services.v1.handle_authetication import authenticate_user, create_access_token, create_refresh_token
from app.schemas.auth import Token, User
from app.core.config import settings

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["user_id"], "role": user["role"], "chat_id": user["chat_id"]}
    )
    refresh_token = create_refresh_token(
        data={"sub": user["username"], "user_id": user["user_id"], "role": user["role"], "chat_id": user["chat_id"]}
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }




