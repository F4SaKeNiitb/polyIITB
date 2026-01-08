from sqlalchemy.orm import Session
from typing import Optional
from ..models.user import User, generate_referral_code
from ..schemas.user import UserCreate
from ..utils.security import get_password_hash
from ..config import settings


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user with hashed password and starting balance."""
    hashed_password = get_password_hash(user_data.password)
    
    # Generate unique referral code
    referral_code = generate_referral_code()
    while db.query(User).filter(User.referral_code == referral_code).first():
        referral_code = generate_referral_code()
    
    # Check if referral code was provided and find referrer
    referred_by = None
    if user_data.referral_code:
        referrer = db.query(User).filter(User.referral_code == user_data.referral_code).first()
        if referrer:
            referred_by = referrer.id
            # Give referrer bonus coins
            referrer.balance += 10000
    
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        balance=settings.starting_balance,
        referral_code=referral_code,
        referred_by=referred_by
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_referral_code(db: Session, referral_code: str) -> Optional[User]:
    """Get a user by their referral code."""
    return db.query(User).filter(User.referral_code == referral_code).first()


def update_user_balance(db: Session, user: User, amount: int) -> User:
    """Update user balance (positive for credit, negative for debit)."""
    user.balance += amount
    db.commit()
    db.refresh(user)
    return user
