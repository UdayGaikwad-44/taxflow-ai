from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.transactions import router as transactions_router
from app.routes.receipts import router as receipts_router
from app.routes.matches import router as matches_router
from app.routes.tds import router as tds_router
from app.routes.deductions import router as deductions_router
from app.routes.tax import router as tax_router
from app.routes.gst import router as gst_router
from app.routes.advance_tax import router as advance_tax_router
from app.routes.upload import router as upload_router
from app.routes.report import router as report_router
from app.routes.notifications import router as notifications_router
from app.routes.ai_chat import router as ai_router

api_router = APIRouter()

api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(transactions_router, tags=["transactions"])
api_router.include_router(receipts_router, tags=["receipts"])
api_router.include_router(matches_router, tags=["matches"])
api_router.include_router(tds_router, tags=["tds"])
api_router.include_router(deductions_router, tags=["deductions"])
api_router.include_router(tax_router, tags=["tax"])
api_router.include_router(gst_router, prefix="/gst", tags=["gst"])
api_router.include_router(advance_tax_router, tags=["advance-tax"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(report_router, prefix="/report", tags=["report"])
api_router.include_router(notifications_router, tags=["notifications"])
api_router.include_router(ai_router, tags=["ai"])
