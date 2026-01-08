from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..database import get_db
from ..schemas.position import PositionResponse
from ..schemas.order import OrderResponse
from ..utils.security import get_current_user
from ..models.user import User
from ..models.position import Position
from ..models.order import Order
from ..models.market import Market

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all positions for the current user."""
    # Use joinedload to prevent N+1 queries - fetch market data in single query
    positions = db.query(Position).filter(
        Position.user_id == current_user.id
    ).options(
        joinedload(Position.market)
    ).all()
    
    # Build response with enriched market data (already loaded via joinedload)
    result = []
    for pos in positions:
        # Only include positions with actual shares
        if pos.yes_shares > 0 or pos.no_shares > 0:
            pos_dict = {
                "id": pos.id,
                "user_id": pos.user_id,
                "market_id": pos.market_id,
                "yes_shares": pos.yes_shares,
                "no_shares": pos.no_shares,
                "avg_yes_price": pos.avg_yes_price,
                "avg_no_price": pos.avg_no_price,
                "created_at": pos.created_at,
                "updated_at": pos.updated_at,
                "market_title": pos.market.title if pos.market else None,
                "current_yes_price": pos.market.yes_price if pos.market else None,
                "current_no_price": pos.market.no_price if pos.market else None
            }
            result.append(PositionResponse(**pos_dict))
    
    return result


@router.get("/history", response_model=List[OrderResponse])
async def get_trade_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trade history for the current user."""
    # Use index on user_id and created_at for efficient query
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    return orders


@router.get("/summary")
async def get_portfolio_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio summary for the current user."""
    # Use joinedload to prevent N+1 queries
    positions = db.query(Position).filter(
        Position.user_id == current_user.id
    ).options(
        joinedload(Position.market)
    ).all()
    
    total_invested = 0.0
    current_value = 0.0
    active_positions = 0
    
    for pos in positions:
        if pos.market:
            # Only count positions with shares
            if pos.yes_shares > 0 or pos.no_shares > 0:
                active_positions += 1
                
                # Calculate value based on current market prices
                yes_value = pos.yes_shares * pos.market.yes_price
                no_value = pos.no_shares * pos.market.no_price
                current_value += yes_value + no_value
                
                # Calculate invested amount based on average purchase price
                yes_invested = pos.yes_shares * pos.avg_yes_price
                no_invested = pos.no_shares * pos.avg_no_price
                total_invested += yes_invested + no_invested
    
    profit_loss = current_value - total_invested
    profit_loss_pct = (profit_loss / total_invested * 100) if total_invested > 0 else 0
    
    return {
        "balance": round(current_user.balance, 2),
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "profit_loss": round(profit_loss, 2),
        "profit_loss_pct": round(profit_loss_pct, 2),
        "total_positions": active_positions,
        "total_equity": round(current_user.balance + current_value, 2)
    }
