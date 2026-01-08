from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class OrderSide(str, enum.Enum):
    """Order side - betting YES or NO."""
    YES = "yes"
    NO = "no"


class OrderType(str, enum.Enum):
    """Order type - buy or sell shares."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"


class Order(Base):
    """Order model for trades."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False, index=True)
    
    side = Column(String(10), nullable=False)  # yes or no
    order_type = Column(String(10), nullable=False)  # buy or sell
    quantity = Column(Integer, nullable=False)  # Number of shares
    price = Column(Float, nullable=False)  # Price per share at execution
    total_cost = Column(Float, nullable=False)  # Total cost of order
    
    status = Column(String(20), default=OrderStatus.PENDING.value)
    filled_quantity = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    market = relationship("Market", back_populates="orders")
    
    # Composite index for common query patterns
    __table_args__ = (
        Index('idx_order_user_market', 'user_id', 'market_id'),
        Index('idx_order_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Order {self.order_type} {self.quantity}x {self.side} @ {self.price}>"
