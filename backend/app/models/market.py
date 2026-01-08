from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class MarketStatus(str, enum.Enum):
    """Market status enum."""
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"


class MarketCategory(str, enum.Enum):
    """Market category enum."""
    POLITICS = "politics"
    SPORTS = "sports"
    CRYPTO = "crypto"
    ENTERTAINMENT = "entertainment"
    SCIENCE = "science"
    BUSINESS = "business"
    OTHER = "other"


class Market(Base):
    """Market model for prediction events."""
    
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default=MarketCategory.OTHER.value, index=True)
    image_url = Column(String(500), nullable=True)
    
    # Trading info
    yes_price = Column(Float, default=0.5)  # Price of YES shares (0.0 - 1.0)
    no_price = Column(Float, default=0.5)   # Price of NO shares (0.0 - 1.0)
    total_volume = Column(Float, default=0.0)  # Total trading volume
    liquidity = Column(Float, default=1000.0)  # AMM liquidity pool
    
    # Status and resolution
    status = Column(String(20), default=MarketStatus.OPEN.value, index=True)
    resolution_date = Column(DateTime(timezone=True), nullable=True)
    resolved_outcome = Column(String(10), nullable=True)  # "yes" or "no"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="market")
    positions = relationship("Position", back_populates="market")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_market_status_category', 'status', 'category'),
    )
    
    def __repr__(self):
        return f"<Market {self.title[:30]}...>"
