import os
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models import Stamp


class StampCreate(BaseModel):
    product_name: str
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    image_url: Optional[str] = None
    theme: Optional[str] = None
    shape_descriptor: Optional[str] = None
    sentiments: Optional[str] = None
    location: Optional[str] = None

    @field_validator("product_name")
    @classmethod
    def product_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("product_name is required and cannot be empty")
        return v.strip()


class StampUpdate(BaseModel):
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    image_url: Optional[str] = None
    theme: Optional[str] = None
    shape_descriptor: Optional[str] = None
    sentiments: Optional[str] = None
    location: Optional[str] = None

    @field_validator("product_name")
    @classmethod
    def product_name_not_empty(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("product_name cannot be empty")
            return v.strip()
        return v


class StampResponse(BaseModel):
    id: int
    product_name: str
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    image_url: Optional[str] = None
    theme: Optional[str] = None
    shape_descriptor: Optional[str] = None
    sentiments: Optional[str] = None
    location: Optional[str] = None

    class Config:
        from_attributes = True


class AIAnalysisRequest(BaseModel):
    """Schema for AI analysis response — fields are all optional."""

    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    theme: Optional[str] = None
    shape_descriptor: Optional[str] = None
    sentiments: Optional[str] = None
