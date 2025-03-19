from pydantic import BaseModel, Field
from typing import Optional

class TypeNumberBase(BaseModel):
    name: str = Field(..., min_length=1)  # Bắt buộc nhập
    description: Optional[str] = None  # Hoàn toàn tùy chọn
    booking_expiration: Optional[int] = None  # Hoàn toàn tùy chọn

class TypeNumberCreate(TypeNumberBase):
    pass

class TypeNumberUpdate(TypeNumberBase):
    pass

class TypeNumberResponse(TypeNumberBase):
    id: int
    booking_expiration : int
    class Config:
        from_attributes = True
