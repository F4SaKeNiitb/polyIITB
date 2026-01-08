# PolyIITB - Prediction Market Platform

A Polymarket clone built with **FastAPI** backend and vanilla JavaScript frontend.

## Features

- 🔐 **JWT Authentication** - Secure user registration and login
- 📊 **Prediction Markets** - Trade on real-world event outcomes
- 💰 **AMM Trading** - Automated market maker for instant trades
- 📈 **Portfolio Tracking** - View your positions and P&L
- 🎨 **Modern UI** - Dark theme with glassmorphism effects

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Open the App

Visit [http://localhost:8000](http://localhost:8000)

### 4. Seed Sample Data

Open browser console and run:
```javascript
seedData()
```

Or use the API directly:
```bash
curl -X POST http://localhost:8000/api/seed
```

## API Documentation

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Default Admin Account

After seeding, you can login with:
- **Email:** admin@polyiitb.com
- **Password:** admin123

## Project Structure

```
polyIITB/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Settings
│   │   ├── database.py      # SQLAlchemy setup
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # API routes
│   │   ├── services/        # Business logic
│   │   └── utils/           # JWT & security
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── index.html
    ├── css/styles.css
    └── js/
        ├── auth.js
        ├── markets.js
        ├── trading.js
        └── main.js
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (get JWT)
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user

### Markets
- `GET /api/markets` - List markets
- `GET /api/markets/{id}` - Get market details
- `POST /api/markets` - Create market (admin)
- `POST /api/markets/{id}/resolve` - Resolve market (admin)

### Trading
- `POST /api/orders` - Place order
- `GET /api/orders` - Get user orders

### Portfolio
- `GET /api/portfolio/positions` - Get positions
- `GET /api/portfolio/summary` - Get portfolio summary
- `GET /api/portfolio/history` - Get trade history

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Pydantic, python-jose
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Auth:** JWT with refresh tokens

## License

MIT
