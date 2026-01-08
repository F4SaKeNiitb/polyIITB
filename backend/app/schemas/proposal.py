from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ProposalCreate(BaseModel):
    """Schema for creating a market proposal."""
    title: str = Field(..., min_length=10, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: str = Field(..., min_length=1, max_length=50)
    resolution_date: datetime


class ProposalResponse(BaseModel):
    """Schema for proposal response."""
    id: int
    title: str
    description: Optional[str]
    category: str
    resolution_date: datetime
    status: str
    admin_notes: Optional[str]
    user_id: int
    username: Optional[str] = None
    market_id: Optional[int]
    created_at: datetime
    reviewed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProposalReview(BaseModel):
    """Schema for admin reviewing a proposal."""
    action: str = Field(..., pattern="^(approve|reject)$")
    admin_notes: Optional[str] = Field(None, max_length=500)
    # Admin can modify these before approving
    title: Optional[str] = Field(None, min_length=10, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    resolution_date: Optional[datetime] = None
