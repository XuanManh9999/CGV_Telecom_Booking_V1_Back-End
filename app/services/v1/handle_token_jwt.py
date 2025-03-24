from fastapi import Request

from app.services.v1 import handle_authetication
from app.utils.utils_token import exact_token


async def access_token_by_refresh_token(request : Request):
    data_token = exact_token(request)
    new_access_token =  handle_authetication.create_access_token(data_token)
    return {"access_token": new_access_token}