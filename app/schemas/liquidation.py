from pydantic import BaseModel

class LiquidationBase(BaseModel):
    phone_numbers: list[str]

class LiquidationRequest(LiquidationBase):
    pass