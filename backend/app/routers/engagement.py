from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Request, HTTPException, Depends

from app.config import DAILY_REWARD_XP, WEEKLY_CHALLENGES
from app.db import db
from app.security import get_current_user
from app.helpers import get_week_start

router = APIRouter()


# ─── DAILY REWARDS ───
@router.get("/rewards/daily")
async def get_daily_reward(user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({"_id": ObjectId(user["_id"])})
    today = datetime.now(timezone.utc).date()
    last_reward = user_doc.get("last_reward_date")
    reward_day = user_doc.get("reward_day", 0)

    already_claimed = False
    if last_reward:
        lr_date = last_reward.date() if isinstance(last_reward, datetime) else last_reward
        already_claimed = lr_date == today
        diff = (today - lr_date).days
        if diff > 1:
            reward_day = 0  # Reset cycle if missed a day

    next_day = (reward_day % 7)
    next_xp = DAILY_REWARD_XP[next_day]

    # Check if user studied today
    studied_today = await db.study_sessions.find_one({
        "user_id": user["_id"],
        "completed_at": {"$gte": datetime(today.year, today.month, today.day, tzinfo=timezone.utc)}
    })

    return {
        "already_claimed": already_claimed,
        "can_claim": bool(studied_today) and not already_claimed,
        "reward_day": next_day + 1,
        "reward_xp": next_xp,
        "studied_today": bool(studied_today),
        "all_rewards": [{"day": i + 1, "xp": xp, "claimed": i < reward_day if not already_claimed else i <= reward_day} for i, xp in enumerate(DAILY_REWARD_XP)],
    }


@router.post("/rewards/claim")
async def claim_daily_reward(user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({"_id": ObjectId(user["_id"])})
    today = datetime.now(timezone.utc).date()
    last_reward = user_doc.get("last_reward_date")
    reward_day = user_doc.get("reward_day", 0)

    if last_reward:
        lr_date = last_reward.date() if isinstance(last_reward, datetime) else last_reward
        if lr_date == today:
            raise HTTPException(status_code=400, detail="Récompense déjà réclamée aujourd'hui")
        if (today - lr_date).days > 1:
            reward_day = 0

    studied = await db.study_sessions.find_one({
        "user_id": user["_id"],
        "completed_at": {"$gte": datetime(today.year, today.month, today.day, tzinfo=timezone.utc)}
    })
    if not studied:
        raise HTTPException(status_code=400, detail="Complète une session d'étude d'abord !")

    xp_reward = DAILY_REWARD_XP[reward_day % 7]
    new_day = (reward_day % 7) + 1
    new_xp = user_doc.get("xp", 0) + xp_reward
    new_level = (new_xp // 500) + 1

    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "xp": new_xp, "level": new_level,
            "reward_day": new_day, "last_reward_date": datetime.now(timezone.utc),
        }}
    )
    return {"xp_earned": xp_reward, "reward_day": new_day, "total_xp": new_xp, "new_level": new_level}


# ─── WEEKLY CHALLENGES ───
async def _challenge_progress(ch, user_id, week_sessions, week_start_dt):
    """Compute current progress for a single challenge definition."""
    if ch["type"] == "sessions":
        return len(week_sessions)
    if ch["type"] == "perfect":
        return sum(1 for s in week_sessions if s.get("percentage") == 100)
    if ch["type"] == "subjects":
        return len(set(s.get("subject_id") for s in week_sessions))
    if ch["type"] == "master":
        return await db.user_card_progress.count_documents({
            "user_id": user_id, "box": 3, "last_reviewed": {"$gte": week_start_dt}
        })
    return 0


@router.get("/challenges")
async def get_challenges(user: dict = Depends(get_current_user)):
    user_id = user["_id"]
    week_start = get_week_start()
    week_start_dt = datetime(week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc)

    week_sessions = await db.study_sessions.find(
        {"user_id": user_id, "completed_at": {"$gte": week_start_dt}}, {"_id": 0}
    ).to_list(500)

    challenges = []
    for ch in WEEKLY_CHALLENGES:
        progress = await _challenge_progress(ch, user_id, week_sessions, week_start_dt)
        completed = progress >= ch["target"]
        claimed = await db.challenge_claims.find_one({
            "user_id": user_id, "challenge_id": ch["id"],
            "week_start": week_start.isoformat(),
        })
        challenges.append({
            **ch, "progress": min(progress, ch["target"]),
            "completed": completed, "claimed": bool(claimed),
        })

    return {"challenges": challenges, "week_start": week_start.isoformat()}


@router.post("/challenges/{challenge_id}/claim")
async def claim_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    user_id = user["_id"]
    week_start = get_week_start()

    ch = next((c for c in WEEKLY_CHALLENGES if c["id"] == challenge_id), None)
    if not ch:
        raise HTTPException(status_code=404, detail="Défi introuvable")

    claimed = await db.challenge_claims.find_one({
        "user_id": user_id, "challenge_id": challenge_id,
        "week_start": week_start.isoformat(),
    })
    if claimed:
        raise HTTPException(status_code=400, detail="Déjà réclamé")

    week_start_dt = datetime(week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc)
    week_sessions = await db.study_sessions.find(
        {"user_id": user_id, "completed_at": {"$gte": week_start_dt}}, {"_id": 0}
    ).to_list(500)

    progress = await _challenge_progress(ch, user_id, week_sessions, week_start_dt)
    if progress < ch["target"]:
        raise HTTPException(status_code=400, detail="Défi pas encore complété")

    xp = ch["xp_reward"]
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    new_xp = user_doc.get("xp", 0) + xp
    new_level = (new_xp // 500) + 1
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"xp": new_xp, "level": new_level}})
    await db.challenge_claims.insert_one({
        "user_id": user_id, "challenge_id": challenge_id,
        "week_start": week_start.isoformat(), "claimed_at": datetime.now(timezone.utc),
    })
    return {"xp_earned": xp, "total_xp": new_xp, "new_level": new_level}


# ─── REFERRAL ───
@router.get("/referral/stats")
async def get_referral_stats(user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({"_id": ObjectId(user["_id"])})
    referral_code = user_doc.get("referral_code", "")
    referral_count = user_doc.get("referral_count", 0)
    referred_users = await db.users.find(
        {"referred_by": user["_id"]}, {"_id": 0, "name": 1, "xp": 1, "level": 1, "created_at": 1}
    ).to_list(100)
    for r in referred_users:
        if isinstance(r.get("created_at"), datetime):
            r["created_at"] = r["created_at"].isoformat()
    return {
        "referral_code": referral_code,
        "referral_count": referral_count,
        "xp_earned_from_referrals": referral_count * 100,
        "referred_users": referred_users,
    }


# ─── SOCIAL SHARING ───
@router.get("/share/profile")
async def get_share_profile(user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({"_id": ObjectId(user["_id"])})
    session_count = await db.study_sessions.count_documents({"user_id": user["_id"]})
    box3 = await db.user_card_progress.count_documents({"user_id": user["_id"], "box": 3})
    text = (
        f"📚 Quikko — Mon profil\n"
        f"👤 {user_doc['name']}\n"
        f"⭐ {user_doc.get('xp', 0)} XP • Niveau {user_doc.get('level', 1)}\n"
        f"🔥 {user_doc.get('streak_count', 0)} jours de streak\n"
        f"📖 {session_count} sessions complétées\n"
        f"🏆 {len(user_doc.get('badges', []))} badges • {box3} cartes maîtrisées\n"
        f"#FlashCards #Révisions #Éducation"
    )
    return {"share_text": text}


@router.post("/share/session")
async def get_share_session(request: Request):
    body = await request.json()
    pct = body.get("percentage", 0)
    correct = body.get("correct", 0)
    total = body.get("total", 0)
    xp = body.get("xp_earned", 0)
    emoji = "🏆" if pct == 100 else ("🎉" if pct >= 80 else ("👍" if pct >= 50 else "💪"))
    text = (
        f"{emoji} Quikko — Résultat\n"
        f"📊 Score : {pct}% ({correct}/{total})\n"
        f"⭐ +{xp} XP gagnés\n"
        f"#Quikko #Révisions"
    )
    return {"share_text": text}
