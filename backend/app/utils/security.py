from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.utils.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def _create_token(*, subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    exp = now + expires_delta
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    # 15 minutes, per spec
    return _create_token(subject=subject, token_type="access", expires_delta=timedelta(minutes=15))


def create_refresh_token(subject: str) -> str:
    # 7 days, per spec
    return _create_token(subject=subject, token_type="refresh", expires_delta=timedelta(days=7))


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

