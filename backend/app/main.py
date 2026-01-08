from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pathlib import Path
from .database import init_db
from .routers import auth_router, markets_router, orders_router, portfolio_router, users_router

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="PolyIITB - Prediction Market",
    description="A Polymarket clone built with FastAPI",
    version="1.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api")
app.include_router(markets_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")
app.include_router(users_router, prefix="/api")

from .routers.proposals import router as proposals_router
app.include_router(proposals_router, prefix="/api")

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/")
async def serve_frontend():
    """Serve the frontend."""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Welcome to PolyIITB API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Seed data endpoint for development
@app.post("/api/seed")
async def seed_database():
    """Seed the database with sample data (development only)."""
    from .database import SessionLocal
    from .models.user import User
    from .models.market import Market
    from .utils.security import get_password_hash
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    
    try:
        # Create admin user
        admin = db.query(User).filter(User.email == "admin@polyiitb.com").first()
        if not admin:
            admin = User(
                email="admin@polyiitb.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                balance=100000000,  # 100,000,000 coins for admin
                is_admin=True,
                referral_code="ADMIN001"
            )
            db.add(admin)
        
        # Create sample markets
        sample_markets = [
            {
                "title": "Will Bitcoin reach $100,000 by the end of 2026?",
                "description": "This market resolves to YES if the price of Bitcoin (BTC) reaches or exceeds $100,000 USD at any point before December 31, 2026.",
                "category": "crypto",
                "yes_price": 0.65,
                "no_price": 0.35,
                "resolution_date": datetime(2026, 12, 31)
            },
            {
                "title": "Will AI pass the Turing test convincingly by 2027?",
                "description": "Resolves YES if a reputable scientific study confirms an AI system passing the Turing test with human judges.",
                "category": "science",
                "yes_price": 0.45,
                "no_price": 0.55,
                "resolution_date": datetime(2027, 12, 31)
            },
            {
                "title": "Will India win the 2027 Cricket World Cup?",
                "description": "This market resolves to YES if Indian cricket team wins the ICC Cricket World Cup 2027.",
                "category": "sports",
                "yes_price": 0.30,
                "no_price": 0.70,
                "resolution_date": datetime(2027, 11, 30)
            },
            {
                "title": "Will Apple release AR glasses in 2026?",
                "description": "Resolves YES if Apple officially releases augmented reality glasses for consumers in 2026.",
                "category": "business",
                "yes_price": 0.55,
                "no_price": 0.45,
                "resolution_date": datetime(2026, 12, 31)
            },
            {
                "title": "Will the next Marvel movie gross over $1 billion?",
                "description": "Resolves YES if the next Marvel Cinematic Universe film grosses over $1 billion worldwide at the box office.",
                "category": "entertainment",
                "yes_price": 0.40,
                "no_price": 0.60,
                "resolution_date": datetime(2026, 6, 30)
            }
        ]
        
        for market_data in sample_markets:
            existing = db.query(Market).filter(Market.title == market_data["title"]).first()
            if not existing:
                market = Market(**market_data)
                db.add(market)
        
        db.commit()
        return {"message": "Database seeded successfully"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
