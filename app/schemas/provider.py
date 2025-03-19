from pydantic import BaseModel
from typing import Optional, List

class ProviderBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProviderCreate(ProviderBase):
    pass # ke thua

class ProviderUpdate(ProviderBase):
    pass

class ProviderResponse(ProviderBase):
    id: int
    class Config:
        from_attributes = True