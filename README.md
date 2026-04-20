# TaxFlow AI

AI-powered tax optimization engine for **Indian freelancers** (₹ context).

## Structure

- `backend/`: FastAPI + SQLAlchemy + PostgreSQL + JWT (Google OAuth scaffold)
- `frontend/`: React + Vite + Tailwind + react-router-dom

## Run (Docker)

1. Copy env:
   - `cp .env.example .env`
2. Start:
   - `docker compose up --build`

Backend health: `http://localhost:8000/health`  
Frontend: `http://localhost:5173`

