from pydantic import BaseModel, Field
from datetime import date



class ReportBase(BaseModel):
    date_report: date = Field(default_factory=date.today)

class ReportRequest(ReportBase):
    pass

class ProviderResponse(ReportBase):
    id: int

    class Config:
        from_attributes = True
