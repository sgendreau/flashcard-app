from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.db import db
from app.security import get_current_user

router = APIRouter()


@router.get("/sync/status")
async def get_sync_status(user: dict = Depends(get_current_user)):
    user_id = user["_id"]
    card_count = await db.user_card_progress.count_documents({"user_id": user_id})
    session_count = await db.study_sessions.count_documents({"user_id": user_id})
    last_session = await db.study_sessions.find_one(
        {"user_id": user_id}, {"_id": 0, "completed_at": 1},
        sort=[("completed_at", -1)]
    )
    last_sync = last_session["completed_at"].isoformat() if last_session and isinstance(last_session.get("completed_at"), datetime) else None
    return {
        "synced": True, "card_progress_count": card_count,
        "session_count": session_count, "last_activity": last_sync,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }
