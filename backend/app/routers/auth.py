from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.db import db
from app.schemas import RegisterInput, LoginInput
from app.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, get_current_user,
)
from app.helpers import generate_referral_code, user_response

router = APIRouter()


@router.post("/auth/register")
async def register(input: RegisterInput):
    email = input.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    user_doc = {
        "email": email, "password_hash": hash_password(input.password),
        "name": input.name.strip(), "role": "student",
        "xp": 0, "level": 1, "streak_count": 0,
        "last_study_date": None, "badges": [],
        "grade_level": None, "notification_enabled": True, "notification_hour": 18,
        "reward_day": 0, "last_reward_date": None,
        "referral_code": generate_referral_code(), "referred_by": None, "referral_count": 0,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Handle referral
    if input.referral_code:
        referrer = await db.users.find_one({"referral_code": input.referral_code.upper().strip()})
        if referrer:
            ref_id = str(referrer["_id"])
            await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"referred_by": ref_id, "xp": 100, "level": 1}})
            await db.users.update_one(
                {"_id": referrer["_id"]},
                {"$inc": {"xp": 100, "referral_count": 1}}
            )
            ref_new_xp = referrer.get("xp", 0) + 100
            ref_new_level = (ref_new_xp // 500) + 1
            await db.users.update_one({"_id": referrer["_id"]}, {"$set": {"level": ref_new_level}})
            user_doc["xp"] = 100

    return {
        "user": user_response(user_doc, user_id),
        "access_token": create_access_token(user_id, email),
        "refresh_token": create_refresh_token(user_id),
    }


@router.post("/auth/login")
async def login(input: LoginInput):
    email = input.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(input.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    user_id = str(user["_id"])
    return {
        "user": user_response(user, user_id),
        "access_token": create_access_token(user_id, email),
        "refresh_token": create_refresh_token(user_id),
    }


@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user_response(user, user["_id"])}


@router.post("/auth/logout")
async def logout():
    return {"message": "Déconnexion réussie"}
