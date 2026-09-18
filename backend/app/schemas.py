import os
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator

from app.models import Stamp


class StampCreate(BaseModel):
    product_name: str
    item_number: Optional[str] = None
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    image_url: Optional[str] = None
    theme: Optional[str] = None
    shape_descriptor: Optional[str] = None
    sentiments: Optional[str] = None
    location: Optional[str] = None
    location_id: Optional[int] = None
    cabinet: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None

    @field_validator("product_name")
    @classmethod
    def product_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("product_name is required and cannot be empty")
        return v.strip()


class StampUpdate(BaseModel):
    product_name: Optional[str] = None
    item_number: Optional[str] = None
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    image_url: Optional[str] = None
    theme: Optional[str] = None
    shape_descriptor: Optional[str] = None
    sentiments: Optional[str] = None
    location: Optional[str] = None
    location_id: Optional[int] = None
    cabinet: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None

    @field_validator("product_name")
    @classmethod
    def product_name_not_empty(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("product_name cannot be empty")
            return v.strip()
        return v


class LocationBase(BaseModel):
    cabinet: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None

    @field_validator("cabinet", "shelf", "bin")
    @classmethod
    def clean_location_part(cls, v):
        if v is None:
            return None
        v = v.strip()
        return v or None

    @model_validator(mode="after")
    def location_not_empty(self):
        if not any((self.cabinet, self.shelf, self.bin)):
            raise ValueError("At least one location field is required")
        return self


class LocationCreate(LocationBase):
    pass


class LocationUpdate(LocationBase):
    pass


class LocationResponse(LocationBase):
    id: int

    class Config:
        from_attributes = True


class StampResponse(BaseModel):
    id: int
    item_number: Optional[str] = None
    product_name: str
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    image_url: Optional[str] = None
    theme: Optional[str] = None
    shape_descriptor: Optional[str] = None
    sentiments: Optional[str] = None
    location: Optional[str] = None
    location_id: Optional[int] = None
    cabinet: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None

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
