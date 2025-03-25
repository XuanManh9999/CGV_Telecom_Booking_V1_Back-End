from fastapi import Request

from app.services.v1 import handle_authetication
from app.utils.utils_token import exact_token


async def access_token_by_refresh_token(request : Request):
    data_token = exact_token(request)
    data = {"sub": data_token["user_name"], "user_id": data_token["user_id"], "role": data_token["role"], "chat_id": data_token["chat_id"]}
    new_access_token =  handle_authetication.create_access_token(data)
    return {"access_token": new_access_token}