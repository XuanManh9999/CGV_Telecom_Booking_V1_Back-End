from fastapi import APIRouter, Request
from app.services.v1 import handle_token_jwt


router = APIRouter(
    tags=["Token JWT"],
)

@router.get("/access_token_by_refresh_token")
async def access_token_by_refresh_token(request : Request):
    return await handle_token_jwt.access_token_by_refresh_token(request)
