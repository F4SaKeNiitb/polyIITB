from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PositionResponse(BaseModel):
    """Schema for position response."""
    id: int
    user_id: int
    market_id: int
    yes_shares: int
    no_shares: int
    avg_yes_price: float
    avg_no_price: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed fields for display
    market_title: Optional[str] = None
    current_yes_price: Optional[float] = None
    current_no_price: Optional[float] = None
    
    class Config:
        from_attributes = True
