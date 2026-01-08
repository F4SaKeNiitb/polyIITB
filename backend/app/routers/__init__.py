from .auth import router as auth_router
from .markets import router as markets_router
from .orders import router as orders_router
from .portfolio import router as portfolio_router
from .users import router as users_router
from .proposals import router as proposals_router

__all__ = [
    "auth_router",
    "markets_router", 
    "orders_router",
    "portfolio_router",
    "users_router",
    "proposals_router"
]
