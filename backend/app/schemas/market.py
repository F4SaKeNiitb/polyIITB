from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from ..models.market import MarketCategory, MarketStatus


class MarketCreate(BaseModel):
    """Schema for market creation."""
    title: str = Field(..., min_length=10, max_length=500)
    description: Optional[str] = None
    category: str = MarketCategory.OTHER.value
    image_url: Optional[str] = Field(None, max_length=500)
    resolution_date: Optional[datetime] = None
    liquidity: float = Field(default=1000.0, ge=100.0, le=1000000.0)
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        valid_categories = [c.value for c in MarketCategory]
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {valid_categories}')
        return v


class MarketResponse(BaseModel):
    """Schema for market response."""
    id: int
    title: str
    description: Optional[str]
    category: str
    image_url: Optional[str]
    yes_price: float
    no_price: float
    total_volume: float
    liquidity: float
    status: str
    resolution_date: Optional[datetime]
    resolved_outcome: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MarketUpdate(BaseModel):
    """Schema for market update."""
    title: Optional[str] = Field(None, min_length=10, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    resolution_date: Optional[datetime] = None
    status: Optional[str] = None


class MarketResolve(BaseModel):
    """Schema for market resolution."""
    outcome: str = Field(..., pattern="^(yes|no)$")
