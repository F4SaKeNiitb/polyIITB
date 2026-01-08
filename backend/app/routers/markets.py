from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..schemas.market import MarketCreate, MarketResponse, MarketUpdate, MarketResolve
from ..services.market import create_market, get_market, get_markets, update_market, get_market_stats
from ..services.trading import trading_engine
from ..utils.security import get_current_user, get_current_admin_user
from ..models.user import User
from ..models.market import MarketStatus

router = APIRouter(prefix="/markets", tags=["Markets"])


@router.get("", response_model=List[MarketResponse])
async def list_markets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get a list of all markets with optional filtering."""
    markets = get_markets(db, skip=skip, limit=limit, category=category, status=status)
    return markets


@router.get("/stats")
async def market_stats(db: Session = Depends(get_db)):
    """Get overall market statistics."""
    return get_market_stats(db)


@router.get("/{market_id}", response_model=MarketResponse)
async def get_market_by_id(market_id: int, db: Session = Depends(get_db)):
    """Get a specific market by ID."""
    market = get_market(db, market_id)
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    return market


@router.post("", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_new_market(
    market_data: MarketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Allow any authenticated user
):
    """Create a new prediction market (admin only)."""
    market = create_market(db, market_data)
    return market


@router.put("/{market_id}", response_model=MarketResponse)
async def update_market_by_id(
    market_id: int,
    market_data: MarketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a market (admin only)."""
    market = get_market(db, market_id)
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    updated_market = update_market(db, market, market_data)
    return updated_market


@router.post("/{market_id}/resolve")
async def resolve_market(
    market_id: int,
    resolution: MarketResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Resolve a market with the given outcome (admin only)."""
    market = get_market(db, market_id)
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    if market.status == MarketStatus.RESOLVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market already resolved"
        )
    
    settled_count, error = trading_engine.resolve_market(db, market, resolution.outcome)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error
        )
    
    return {
        "message": f"Market resolved as {resolution.outcome.upper()}",
        "settled_positions": settled_count
    }


@router.delete("/{market_id}", status_code=status.HTTP_200_OK)
async def delete_market(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a market (admin only). Also deletes related orders and positions."""
    from ..models.order import Order
    from ..models.position import Position
    
    market = get_market(db, market_id)
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Delete related orders first
    db.query(Order).filter(Order.market_id == market_id).delete()
    
    # Delete related positions
    db.query(Position).filter(Position.market_id == market_id).delete()
    
    # Delete the market
    db.delete(market)
    db.commit()
    
    return {"message": f"Market '{market.title}' deleted successfully"}
