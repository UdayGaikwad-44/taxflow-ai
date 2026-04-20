"""
Compatibility package to match requested /backend/routes structure.
Primary implementation lives in backend/app/routes.
"""

from app.routes import api_router  # re-export for convenience

__all__ = ["api_router"]

