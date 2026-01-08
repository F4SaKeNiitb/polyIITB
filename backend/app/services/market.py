from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.market import Market, MarketStatus, MarketCategory
from ..schemas.market import MarketCreate, MarketUpdate


def create_market(db: Session, market_data: MarketCreate) -> Market:
    """Create a new prediction market."""
    db_market = Market(
        title=market_data.title,
        description=market_data.description,
        category=market_data.category,
        image_url=market_data.image_url,
        resolution_date=market_data.resolution_date,
        liquidity=market_data.liquidity,
        yes_price=0.5,
        no_price=0.5
    )
    db.add(db_market)
    db.commit()
    db.refresh(db_market)
    return db_market


def get_market(db: Session, market_id: int) -> Optional[Market]:
    """Get a market by ID."""
    return db.query(Market).filter(Market.id == market_id).first()


def get_markets(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    status: Optional[str] = None
) -> List[Market]:
    """Get a list of markets with optional filtering."""
    query = db.query(Market)
    
    if category:
        query = query.filter(Market.category == category)
    if status:
        query = query.filter(Market.status == status)
    
    return query.order_by(Market.created_at.desc()).offset(skip).limit(limit).all()


def update_market(db: Session, market: Market, market_data: MarketUpdate) -> Market:
    """Update a market."""
    update_data = market_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(market, field, value)
    db.commit()
    db.refresh(market)
    return market


def get_market_stats(db: Session) -> dict:
    """Get overall market statistics."""
    total_markets = db.query(Market).count()
    open_markets = db.query(Market).filter(Market.status == MarketStatus.OPEN.value).count()
    resolved_markets = db.query(Market).filter(Market.status == MarketStatus.RESOLVED.value).count()
    
    # Total volume across all markets
    from sqlalchemy import func
    total_volume = db.query(func.sum(Market.total_volume)).scalar() or 0
    
    return {
        "total_markets": total_markets,
        "open_markets": open_markets,
        "resolved_markets": resolved_markets,
        "total_volume": total_volume
    }
