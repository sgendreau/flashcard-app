from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.config import GRADE_LEVELS
from app.db import db
from app.schemas import UpdateGradeInput, UpdateNotificationInput, UpdateThemeInput
from app.security import get_current_user

router = APIRouter()


@router.put("/user/grade")
async def update_grade(input: UpdateGradeInput, user: dict = Depends(get_current_user)):
    if input.grade_level and input.grade_level not in GRADE_LEVELS:
        raise HTTPException(status_code=400, detail="Niveau invalide")
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"grade_level": input.grade_level}}
    )
    return {"grade_level": input.grade_level}


@router.put("/user/notifications")
async def update_notifications(input: UpdateNotificationInput, user: dict = Depends(get_current_user)):
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"notification_enabled": input.notification_enabled, "notification_hour": input.notification_hour}}
    )
    return {"notification_enabled": input.notification_enabled, "notification_hour": input.notification_hour}


@router.put("/user/theme")
async def update_theme(input: UpdateThemeInput, user: dict = Depends(get_current_user)):
    if input.theme not in ["light", "dark"]:
        raise HTTPException(status_code=400, detail="Thème invalide")
    await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"theme": input.theme}})
    return {"theme": input.theme}
