from pydantic import BaseModel

class BookingBase(BaseModel):
    user_name: str
    id_phone_numbers: list[int]

class BookingRequest(BookingBase):
    pass
