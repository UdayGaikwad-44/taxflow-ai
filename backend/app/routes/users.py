from fastapi import APIRouter, Depends

from app.utils.auth import get_current_user_id

router = APIRouter(prefix="/users")


# Endpoint 5
@router.get("/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    return {"id": user_id, "currency": "INR", "message": "Profile placeholder"}


# Endpoint 6
@router.put("/me")
def update_me(user_id: str = Depends(get_current_user_id)):
    return {"ok": True, "id": user_id, "message": "Update profile placeholder"}

