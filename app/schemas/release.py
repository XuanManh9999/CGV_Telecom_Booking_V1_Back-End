from pydantic import BaseModel
from typing import List

class ReleaseItem(BaseModel):
    phone_number: str
    contract_code: str

class ReleaseRequest(BaseModel):
    data_releases: List[ReleaseItem]
