from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.order import OrderCreate, OrderResponse
from ..services.market import get_market
from ..services.trading import trading_engine
from ..utils.security import get_current_user
from ..models.user import User
from ..models.order import Order
from ..models.market import MarketStatus

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Place a new order (buy or sell shares)."""
    # Get the market
    market = get_market(db, order_data.market_id)
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Check if market is open
    if market.status != MarketStatus.OPEN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market is not open for trading"
        )
    
    # Execute the order
    if order_data.order_type == "buy":
        order, error = trading_engine.execute_buy_order(
            db, current_user, market, order_data.side, order_data.quantity
        )
    else:
        order, error = trading_engine.execute_sell_order(
            db, current_user, market, order_data.side, order_data.quantity
        )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return order


@router.get("", response_model=List[OrderResponse])
async def get_user_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    market_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's orders."""
    query = db.query(Order).filter(Order.user_id == current_user.id)
    
    if market_id:
        query = query.filter(Order.market_id == market_id)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific order by ID."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order
