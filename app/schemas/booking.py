from pydantic import BaseModel

class BookingBase(BaseModel):
    id_phone_numbers: list[int]

class BookingRequest(BookingBase):
    pass
