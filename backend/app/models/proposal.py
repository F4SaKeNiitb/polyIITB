from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class ProposalStatus(str, enum.Enum):
    """Status of a market proposal."""
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class MarketProposal(Base):
    """Model for user-submitted market proposals awaiting admin approval."""
    
    __tablename__ = "market_proposals"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    resolution_date = Column(DateTime, nullable=False)
    
    # Proposal status
    status = Column(String(20), default=ProposalStatus.pending.value, index=True)
    admin_notes = Column(Text, nullable=True)  # Admin can add notes on rejection
    
    # User who submitted
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", backref="proposals")
    
    # If approved, link to the created market
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<MarketProposal {self.id}: {self.title[:30]}>"
