"""
Alias module to match expected import path `app.models.users`.
Primary model lives in `app.models.user`.
"""

from app.models.user import User

__all__ = ["User"]

