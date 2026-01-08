from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import secrets
import string
from ..database import Base


def generate_referral_code():
    """Generate a unique 8-character referral code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


class User(Base):
    """User model for authentication and trading."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Integer, default=10000)  # Coins balance (100 coins = $1)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Referral system
    referral_code = Column(String(8), unique=True, index=True, nullable=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    positions = relationship("Position", back_populates="user")
    referrer = relationship("User", remote_side=[id], foreign_keys=[referred_by])
    
    def __repr__(self):
        return f"<User {self.username}>"
