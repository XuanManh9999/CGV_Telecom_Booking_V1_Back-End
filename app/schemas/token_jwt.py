from pydantic import BaseModel
class TokenJWTBase(BaseModel):
    refresh_token: str

class TokenJWTRequest(BaseModel):
    pass
class TokenJWTResponse(BaseModel):
    access_token: str