from pydantic import BaseModel


class PhoneNumberBase(BaseModel):
    phone_number: str
    provider_id: int
    type_id: int
    installation_fee: float
    maintenance_fee: float
    vanity_number_fee: float

class PhoneNumberCreate(PhoneNumberBase):
    pass

class PhoneNumberUpdate(PhoneNumberBase):
    pass

class PhoneNumberResponse(PhoneNumberBase):
    id: int
    status: str
    class Config:
        from_attributes = True