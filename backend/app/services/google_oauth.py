"""
Google OAuth 2.0 service for TaxFlow AI.
Flow:
  1. Frontend redirects user to /api/auth/google/start → get authorization URL
  2. Google redirects back to redirect_uri with ?code=... 
  3. Backend calls /api/auth/google/callback?code=... → exchange code, verify id_token, upsert user, return JWT
"""
import httpx
from urllib.parse import urlencode
from dataclasses import dataclass
from typing import Optional

from app.utils.settings import settings


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = "openid email profile"


@dataclass(frozen=True)
class GoogleOAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str


def get_google_oauth_config() -> GoogleOAuthConfig:
    return GoogleOAuthConfig(
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
        redirect_uri=settings.google_oauth_redirect_uri,
    )


def build_google_auth_url() -> str:
    """Build the Google OAuth authorization URL to redirect the user to."""
    cfg = get_google_oauth_config()
    params = {
        "client_id": cfg.client_id,
        "redirect_uri": cfg.redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access_token + id_token."""
    cfg = get_google_oauth_config()
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": cfg.client_id,
                "client_secret": cfg.client_secret,
                "redirect_uri": cfg.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_google_user_info(access_token: str) -> dict:
    """Fetch user profile from Google using access token."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
