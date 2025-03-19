from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PhoneNumberBase(BaseModel):
    phone_number: str
    status: str
    provider_id: int
    type_id: int

class PhoneNumberCreate(PhoneNumberBase):
    pass

class PhoneNumberUpdate(PhoneNumberBase):
    status: Optional[str] = None

class PhoneNumberResponse(PhoneNumberBase):
    id: int
    booked_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
