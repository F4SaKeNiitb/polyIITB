from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class OrderCreate(BaseModel):
    """Schema for order creation."""
    market_id: int = Field(..., ge=1)
    side: str = Field(..., pattern="^(yes|no)$")  # yes or no
    order_type: str = Field(..., pattern="^(buy|sell)$")  # buy or sell
    quantity: int = Field(..., ge=1, le=10000)  # Max 10,000 shares per order


class OrderResponse(BaseModel):
    """Schema for order response."""
    id: int
    user_id: int
    market_id: int
    side: str
    order_type: str
    quantity: int
    price: float
    total_cost: float
    status: str
    filled_quantity: int
    created_at: datetime
    executed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
