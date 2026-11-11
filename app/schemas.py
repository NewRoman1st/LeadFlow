from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

LeadStatus = Literal["new", "in_progress", "completed", "rejected"]


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=5, max_length=30)
    service: str = Field(min_length=2, max_length=120)
    message: str = Field(default="", max_length=2000)


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    service: str
    message: str
    status: LeadStatus
    created_at: str
    updated_at: str
