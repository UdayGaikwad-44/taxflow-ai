from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.google_oauth import (
    build_google_auth_url,
    exchange_code_for_tokens,
    get_google_user_info,
    get_google_oauth_config,
)
from app.models.user import User
from app.utils.db import get_db
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_token,
)
from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/auth")


class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    user_type: Literal["freelancer", "director", "salaried"]


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


def _itr_form_for(user_type: str) -> str:
    if user_type == "director":
        return "ITR-3"
    if user_type == "freelancer":
        return "ITR-3 or ITR-4"
    return "ITR-1"


def _user_out(u: User) -> dict:
    return {
        "id": str(u.id),
        "name": u.full_name,
        "email": u.email,
        "user_type": u.user_type,
        "itr_form": u.itr_form,
    }


# POST /api/auth/register
@router.post("/register")
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        email=str(payload.email).lower(),
        full_name=payload.name,
        hashed_password=hash_password(payload.password),
        user_type=payload.user_type,
        itr_form=_itr_form_for(payload.user_type),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_out(user),
    }


# POST /api/auth/login
@router.post("/login")
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_out(user),
    }


# POST /api/auth/refresh
@router.post("/refresh")
async def refresh(payload: RefreshIn):
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if decoded.get("type") != "refresh" or not decoded.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return {"access_token": create_access_token(subject=str(decoded["sub"]))}


# GET /api/auth/me
@router.get("/me")
async def me(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_out(user)


# GET /api/auth/google/start — returns Google OAuth authorization URL
@router.get("/google/start")
def google_start():
    """
    Returns the Google OAuth URL to redirect the user to for sign-in.
    Frontend should redirect the user to the returned `auth_url`.
    """
    cfg = get_google_oauth_config()
    if not cfg.client_id or cfg.client_id == "placeholder":
        raise HTTPException(
            status_code=503,
            detail="Google OAuth not configured. Set GOOGLE_OAUTH_CLIENT_ID and related vars in .env"
        )
    auth_url = build_google_auth_url()
    return {
        "ok": True,
        "auth_url": auth_url,
        "redirect_uri": cfg.redirect_uri,
    }


# POST /api/auth/google/callback — exchange code, upsert user, return JWT
@router.post("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the frontend after Google redirects back with ?code=...
    Exchanges the code for tokens, fetches user info, upserts the user in DB,
    and returns a TaxFlow JWT pair.
    """
    cfg = get_google_oauth_config()
    if not cfg.client_id or cfg.client_id == "placeholder":
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    try:
        tokens = await exchange_code_for_tokens(code)
        user_info = await get_google_user_info(tokens["access_token"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {str(e)}")

    google_sub = user_info.get("id") or user_info.get("sub")
    email = user_info.get("email", "").lower()
    full_name = user_info.get("name", "")

    if not email or not google_sub:
        raise HTTPException(status_code=400, detail="Google did not return email/sub")

    # Try to find existing user by google_sub first, then by email
    user = await db.scalar(select(User).where(User.google_sub == google_sub))
    if not user:
        user = await db.scalar(select(User).where(User.email == email))

    if user:
        # Update google_sub if not already linked
        if not user.google_sub:
            user.google_sub = google_sub
            await db.commit()
            await db.refresh(user)
    else:
        # Create new user with Google OAuth
        user = User(
            email=email,
            full_name=full_name,
            google_sub=google_sub,
            hashed_password=None,  # No password for OAuth users
            user_type="freelancer",  # Default; can be changed in onboarding
            itr_form="ITR-3 or ITR-4",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_out(user),
        "is_new_user": user.user_type == "freelancer" and not user.hashed_password,
    }
