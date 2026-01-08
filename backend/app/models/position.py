from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Position(Base):
    """Position model for user holdings in a market."""
    
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False, index=True)
    
    yes_shares = Column(Integer, default=0)  # Number of YES shares held
    no_shares = Column(Integer, default=0)   # Number of NO shares held
    avg_yes_price = Column(Float, default=0.0)  # Average purchase price for YES
    avg_no_price = Column(Float, default=0.0)   # Average purchase price for NO
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="positions")
    market = relationship("Market", back_populates="positions")
    
    # Unique constraint - one position per user per market
    __table_args__ = (
        UniqueConstraint('user_id', 'market_id', name='unique_user_market_position'),
    )
    
    def __repr__(self):
        return f"<Position User:{self.user_id} Market:{self.market_id} YES:{self.yes_shares} NO:{self.no_shares}>"
