from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from datetime import datetime
from typing import Optional, Tuple
from ..models.market import Market, MarketStatus
from ..models.order import Order, OrderStatus
from ..models.position import Position
from ..models.user import User
import math


class TradingEngine:
    """
    Automated Market Maker (AMM) trading engine.
    Uses a simplified constant-product formula with proper transaction safety.
    """
    
    @staticmethod
    def calculate_price(shares_yes: float, shares_no: float) -> Tuple[float, float]:
        """
        Calculate current prices based on share distribution.
        Uses formula: price = shares_opposite / (shares_yes + shares_no)
        Ensures prices always sum to 1.0.
        """
        total = shares_yes + shares_no
        if total == 0:
            return 0.5, 0.5
        
        yes_price = shares_no / total
        # Clamp and ensure sum = 1.0
        yes_price = round(min(0.99, max(0.01, yes_price)), 4)
        no_price = round(1.0 - yes_price, 4)
        
        return yes_price, no_price
    
    @staticmethod
    def calculate_price_impact(quantity: int, liquidity: float, side: str, current_price: float) -> float:
        """
        Calculate price impact using logarithmic formula for more realistic AMM behavior.
        Returns the new price after the trade.
        """
        # Use diminishing impact formula: impact decreases as price approaches bounds
        base_impact = quantity / (liquidity * 10)
        
        if side == "yes":
            # Harder to move price as it approaches 0.99
            available_room = 0.99 - current_price
            impact = base_impact * (available_room / 0.49)  # Normalize to half range
            new_price = min(0.99, current_price + impact)
        else:
            # For no side, we reduce the price
            available_room = current_price - 0.01
            impact = base_impact * (available_room / 0.49)
            new_price = max(0.01, current_price - impact)
        
        return round(new_price, 4)
    
    @staticmethod
    def execute_buy_order(
        db: Session,
        user: User,
        market: Market,
        side: str,
        quantity: int
    ) -> Tuple[Optional[Order], Optional[str]]:
        """
        Execute a buy order with proper transaction safety.
        Uses SELECT FOR UPDATE to prevent race conditions.
        Returns (order, error_message).
        """
        try:
            # Lock user and market rows to prevent race conditions
            locked_user = db.execute(
                select(User).where(User.id == user.id).with_for_update()
            ).scalar_one()
            
            locked_market = db.execute(
                select(Market).where(Market.id == market.id).with_for_update()
            ).scalar_one()
            
            # Calculate cost using current price
            current_price = locked_market.yes_price if side == "yes" else locked_market.no_price
            total_cost = current_price * quantity
            
            # Check if user has enough balance
            if locked_user.balance < total_cost:
                return None, f"Insufficient balance. Need ${total_cost:.2f}, have ${locked_user.balance:.2f}"
            
            # Update user balance
            locked_user.balance -= total_cost
            
            # Update market prices with improved impact formula
            if side == "yes":
                new_yes_price = TradingEngine.calculate_price_impact(
                    quantity, locked_market.liquidity, "yes", locked_market.yes_price
                )
                locked_market.yes_price = new_yes_price
                locked_market.no_price = round(1.0 - new_yes_price, 4)
            else:
                new_no_price = TradingEngine.calculate_price_impact(
                    quantity, locked_market.liquidity, "yes", locked_market.no_price
                )
                locked_market.no_price = new_no_price
                locked_market.yes_price = round(1.0 - new_no_price, 4)
            
            locked_market.total_volume += total_cost
            
            # Create order record
            order = Order(
                user_id=locked_user.id,
                market_id=locked_market.id,
                side=side,
                order_type="buy",
                quantity=quantity,
                price=current_price,
                total_cost=total_cost,
                status=OrderStatus.FILLED.value,
                filled_quantity=quantity,
                executed_at=datetime.utcnow()
            )
            db.add(order)
            
            # Update or create position with row locking
            position = db.execute(
                select(Position).where(
                    Position.user_id == locked_user.id,
                    Position.market_id == locked_market.id
                ).with_for_update()
            ).scalar_one_or_none()
            
            if not position:
                position = Position(
                    user_id=locked_user.id,
                    market_id=locked_market.id,
                    yes_shares=0,
                    no_shares=0,
                    avg_yes_price=0,
                    avg_no_price=0
                )
                db.add(position)
                db.flush()  # Get the position ID
            
            # Update position with new shares and calculate weighted average price
            if side == "yes":
                total_shares = position.yes_shares + quantity
                if total_shares > 0:
                    position.avg_yes_price = (
                        (position.avg_yes_price * position.yes_shares) + 
                        (current_price * quantity)
                    ) / total_shares
                position.yes_shares = total_shares
            else:
                total_shares = position.no_shares + quantity
                if total_shares > 0:
                    position.avg_no_price = (
                        (position.avg_no_price * position.no_shares) + 
                        (current_price * quantity)
                    ) / total_shares
                position.no_shares = total_shares
            
            db.commit()
            db.refresh(order)
            
            return order, None
            
        except Exception as e:
            db.rollback()
            return None, f"Transaction failed: {str(e)}"
    
    @staticmethod
    def execute_sell_order(
        db: Session,
        user: User,
        market: Market,
        side: str,
        quantity: int
    ) -> Tuple[Optional[Order], Optional[str]]:
        """
        Execute a sell order with proper transaction safety.
        Uses SELECT FOR UPDATE to prevent race conditions.
        Returns (order, error_message).
        """
        try:
            # Lock user and market rows
            locked_user = db.execute(
                select(User).where(User.id == user.id).with_for_update()
            ).scalar_one()
            
            locked_market = db.execute(
                select(Market).where(Market.id == market.id).with_for_update()
            ).scalar_one()
            
            # Get and lock user's position
            position = db.execute(
                select(Position).where(
                    Position.user_id == locked_user.id,
                    Position.market_id == locked_market.id
                ).with_for_update()
            ).scalar_one_or_none()
            
            if not position:
                return None, "No position to sell"
            
            # Check if user has enough shares
            shares_held = position.yes_shares if side == "yes" else position.no_shares
            if shares_held < quantity:
                return None, f"Insufficient shares. You have {shares_held} shares."
            
            # Calculate payout at current price
            current_price = locked_market.yes_price if side == "yes" else locked_market.no_price
            total_payout = current_price * quantity
            
            # Update user balance
            locked_user.balance += total_payout
            
            # Update market prices (inverse of buy - selling reduces price)
            if side == "yes":
                # Selling YES reduces YES price
                impact = quantity / (locked_market.liquidity * 10)
                available_room = locked_market.yes_price - 0.01
                adjusted_impact = impact * (available_room / 0.49)
                locked_market.yes_price = max(0.01, locked_market.yes_price - adjusted_impact)
                locked_market.yes_price = round(locked_market.yes_price, 4)
                locked_market.no_price = round(1.0 - locked_market.yes_price, 4)
            else:
                impact = quantity / (locked_market.liquidity * 10)
                available_room = locked_market.no_price - 0.01
                adjusted_impact = impact * (available_room / 0.49)
                locked_market.no_price = max(0.01, locked_market.no_price - adjusted_impact)
                locked_market.no_price = round(locked_market.no_price, 4)
                locked_market.yes_price = round(1.0 - locked_market.no_price, 4)
            
            locked_market.total_volume += total_payout
            
            # Create order record
            order = Order(
                user_id=locked_user.id,
                market_id=locked_market.id,
                side=side,
                order_type="sell",
                quantity=quantity,
                price=current_price,
                total_cost=total_payout,
                status=OrderStatus.FILLED.value,
                filled_quantity=quantity,
                executed_at=datetime.utcnow()
            )
            db.add(order)
            
            # Update position
            if side == "yes":
                position.yes_shares -= quantity
            else:
                position.no_shares -= quantity
            
            db.commit()
            db.refresh(order)
            
            return order, None
            
        except Exception as e:
            db.rollback()
            return None, f"Transaction failed: {str(e)}"
    
    @staticmethod
    def resolve_market(
        db: Session,
        market: Market,
        outcome: str
    ) -> Tuple[int, Optional[str]]:
        """
        Resolve a market and pay out winners.
        Processes in batches to handle large numbers of positions.
        Returns (settled_count, error_message).
        """
        try:
            # Lock the market
            locked_market = db.execute(
                select(Market).where(Market.id == market.id).with_for_update()
            ).scalar_one()
            
            locked_market.status = MarketStatus.RESOLVED.value
            locked_market.resolved_outcome = outcome
            
            # Process positions in batches
            batch_size = 500
            offset = 0
            settled_count = 0
            
            while True:
                # Get batch of positions with user data eagerly loaded
                positions = db.query(Position).filter(
                    Position.market_id == locked_market.id
                ).options(
                    joinedload(Position.user)
                ).offset(offset).limit(batch_size).all()
                
                if not positions:
                    break
                
                for position in positions:
                    if outcome == "yes":
                        # YES holders win $1 per share
                        payout = position.yes_shares * 1.0
                    else:
                        # NO holders win $1 per share
                        payout = position.no_shares * 1.0
                    
                    if payout > 0:
                        # Lock the user row for update
                        user = db.execute(
                            select(User).where(User.id == position.user_id).with_for_update()
                        ).scalar_one()
                        user.balance += payout
                        settled_count += 1
                
                offset += batch_size
                # Commit each batch to prevent long-running transactions
                db.flush()
            
            db.commit()
            return settled_count, None
            
        except Exception as e:
            db.rollback()
            return 0, f"Resolution failed: {str(e)}"


trading_engine = TradingEngine()
