# 🚀 PolyIITB Deployment Guide

## Recommended: Render.com (Free Tier)

### Step 1: Push to GitHub

```bash
cd /Users/manish/Downloads/polyIITB

# Initialize git (if not already)
git init

# Add all files
git add .
git commit -m "Initial commit - PolyIITB prediction market"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/polyiitb.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

#### Option A: One-Click Deploy (Recommended)
1. Go to [render.com](https://render.com) and sign up
2. Click **New → Blueprint**
3. Connect your GitHub repo
4. Render reads `render.yaml` and creates everything automatically!

#### Option B: Manual Setup
1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repository
3. Configure:
   | Setting | Value |
   |---------|-------|
   | **Name** | `polyiitb` |
   | **Region** | Singapore (closest to India) |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r backend/requirements.txt` |
   | **Start Command** | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

4. Click **Create Web Service**

### Step 3: Add PostgreSQL Database

1. Go to Render Dashboard → **New → PostgreSQL**
2. Choose **Free** plan (90 days free)
3. Note the **Internal Database URL**
4. Go to your Web Service → **Environment**
5. Add:
   ```
   DATABASE_URL = <paste Internal Database URL>
   SECRET_KEY = your-super-secret-random-string-here
   ```

### Step 4: Initialize Database

After deployment, seed your database:
```bash
curl -X POST https://polyiitb.onrender.com/api/seed
```

### Step 5: Access Your App!

- **URL**: `https://polyiitb.onrender.com`
- **Admin Login**: `admin@polyiitb.com` / `admin123`

---

## Alternative: Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy (from project root)
cd /Users/manish/Downloads/polyIITB
fly launch

# Add PostgreSQL
fly postgres create --name polyiitb-db
fly postgres attach polyiitb-db

# Deploy
fly deploy
```

---

## Alternative: Docker (Self-hosted VPS)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access at http://YOUR_SERVER_IP:8000

# Seed database
curl -X POST http://YOUR_SERVER_IP:8000/api/seed
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | JWT signing key (random 32+ chars) |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│         https://polyiitb.onrender.com       │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│            FastAPI Backend                   │
│   /api/* → API endpoints                    │
│   /static/* → Frontend files                │
│   / → index.html                            │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│          PostgreSQL Database                 │
│   Render Free: 90 days, then $7/month       │
└─────────────────────────────────────────────┘
```

---

## Troubleshooting

### App not loading?
- Check Render logs: Dashboard → Your Service → Logs
- Make sure DATABASE_URL is set correctly

### Database errors?
- Ensure PostgreSQL is connected
- Run seed endpoint: `POST /api/seed`

### Free tier sleeping?
- Render free tier sleeps after 15 min inactivity
- First request takes ~30s to wake up

---

## Cost Summary

| Service | Free Tier | Paid |
|---------|-----------|------|
| **Render Web** | Forever free (sleeps) | $7/month (always on) |
| **Render PostgreSQL** | 90 days free | $7/month |
| **Fly.io** | 3 VMs free | Pay as you go |
