from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

LeadStatus = Literal["new", "in_progress", "completed", "rejected"]


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=5, max_length=30)
    service: str = Field(min_length=2, max_length=120)
    message: str = Field(default="", max_length=2000)

    @field_validator("name", "phone", "service", "message", mode="before")
    @classmethod
    def strip_string_fields(cls, value):
        """Trim surrounding whitespace before validating field lengths."""
        if isinstance(value, str):
            return value.strip()
        return value


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
