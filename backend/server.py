from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, Request, HTTPException, Query
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import bcrypt
import jwt
import string
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from typing import List, Optional
import random

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_ALGORITHM = "HS256"
GRADE_LEVELS = ["6eme", "5eme", "4eme", "3eme", "2nde", "1ere", "terminale"]

def get_jwt_secret():
    return os.environ["JWT_SECRET"]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(hours=24), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def generate_class_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def user_response(user_doc, user_id=None):
    uid = user_id or str(user_doc.get("_id", ""))
    return {
        "id": uid, "email": user_doc["email"], "name": user_doc["name"],
        "xp": user_doc.get("xp", 0), "level": user_doc.get("level", 1),
        "streak_count": user_doc.get("streak_count", 0),
        "badges": user_doc.get("badges", []), "role": user_doc.get("role", "student"),
        "grade_level": user_doc.get("grade_level"),
        "notification_enabled": user_doc.get("notification_enabled", True),
        "notification_hour": user_doc.get("notification_hour", 18),
    }

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ─── PYDANTIC MODELS ───
class RegisterInput(BaseModel):
    name: str
    email: str
    password: str

class LoginInput(BaseModel):
    email: str
    password: str

class CardResult(BaseModel):
    card_id: str
    is_correct: bool

class SubmitStudyInput(BaseModel):
    subject_id: str
    results: List[CardResult]

class CreateFlashcardInput(BaseModel):
    subject_id: str
    question: str
    answer: str
    grade_levels: Optional[List[str]] = None

class UpdateGradeInput(BaseModel):
    grade_level: Optional[str] = None

class UpdateNotificationInput(BaseModel):
    notification_enabled: bool
    notification_hour: int = 18

class CreateClassInput(BaseModel):
    name: str
    is_private: bool = False
    locked_grade: Optional[str] = None

class JoinClassInput(BaseModel):
    code: str

class ShareDeckInput(BaseModel):
    subject_id: str
    name: str

class ImportDeckInput(BaseModel):
    subject_id: str
    cards: List[dict]

class UpdateThemeInput(BaseModel):
    theme: str  # "light" or "dark"

DAILY_REWARD_XP = [25, 50, 75, 100, 150, 200, 300]  # Day 1-7 cycle

WEEKLY_CHALLENGES = [
    {"id": "sessions_5", "type": "sessions", "title": "Marathonien", "description": "Complète 5 sessions cette semaine", "target": 5, "xp_reward": 200, "icon": "albums-outline"},
    {"id": "perfect_2", "type": "perfect", "title": "Sans faute", "description": "Obtiens 100% sur 2 sessions", "target": 2, "xp_reward": 300, "icon": "star-outline"},
    {"id": "subjects_3", "type": "subjects", "title": "Touche-à-tout", "description": "Étudie 3 matières différentes", "target": 3, "xp_reward": 150, "icon": "grid-outline"},
    {"id": "master_5", "type": "master", "title": "Maître absolu", "description": "Déplace 5 cartes en boîte 3", "target": 5, "xp_reward": 250, "icon": "trophy-outline"},
]

def get_week_start():
    today = datetime.now(timezone.utc).date()
    return today - timedelta(days=today.weekday())

# ─── APP SETUP ───
app = FastAPI()
api_router = APIRouter(prefix="/api")

# ═══════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════
@api_router.post("/auth/register")
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
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    return {
        "user": user_response(user_doc, user_id),
        "access_token": create_access_token(user_id, email),
        "refresh_token": create_refresh_token(user_id),
    }

@api_router.post("/auth/login")
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

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return {"user": user_response(user, user["_id"])}

@api_router.post("/auth/logout")
async def logout():
    return {"message": "Déconnexion réussie"}

# ═══════════════════════════════════════════
# USER SETTINGS ROUTES
# ═══════════════════════════════════════════
@api_router.put("/user/grade")
async def update_grade(input: UpdateGradeInput, request: Request):
    user = await get_current_user(request)
    if input.grade_level and input.grade_level not in GRADE_LEVELS:
        raise HTTPException(status_code=400, detail="Niveau invalide")
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"grade_level": input.grade_level}}
    )
    return {"grade_level": input.grade_level}

@api_router.put("/user/notifications")
async def update_notifications(input: UpdateNotificationInput, request: Request):
    user = await get_current_user(request)
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"notification_enabled": input.notification_enabled, "notification_hour": input.notification_hour}}
    )
    return {"notification_enabled": input.notification_enabled, "notification_hour": input.notification_hour}

# ═══════════════════════════════════════════
# SUBJECTS ROUTES
# ═══════════════════════════════════════════
@api_router.get("/subjects")
async def get_subjects(request: Request, grade: Optional[str] = Query(None)):
    user = await get_current_user(request)
    user_grade = grade or user.get("grade_level")
    subjects = await db.subjects.find({}, {"_id": 0}).to_list(100)
    for s in subjects:
        query = {"subject_id": s["id"]}
        if user_grade:
            query["grade_levels"] = user_grade
        count = await db.flashcards.count_documents(query)
        s["card_count"] = count
    # Filter out subjects with 0 cards if grade filter is active
    if user_grade:
        subjects = [s for s in subjects if s["card_count"] > 0]
    return {"subjects": subjects, "grade_levels": GRADE_LEVELS}

# ═══════════════════════════════════════════
# FLASHCARDS ROUTES
# ═══════════════════════════════════════════
@api_router.get("/flashcards/{subject_id}")
async def get_flashcards(subject_id: str, request: Request):
    await get_current_user(request)
    cards = await db.flashcards.find({"subject_id": subject_id}, {"_id": 0}).to_list(500)
    return {"flashcards": cards}

@api_router.post("/flashcards")
async def create_flashcard(input: CreateFlashcardInput, request: Request):
    user = await get_current_user(request)
    card_id = str(ObjectId())
    gl = input.grade_levels if input.grade_levels else list(GRADE_LEVELS)
    card_doc = {
        "id": card_id, "subject_id": input.subject_id,
        "question": input.question.strip(), "answer": input.answer.strip(),
        "grade_levels": gl,
        "created_by": user["_id"], "created_at": datetime.now(timezone.utc),
    }
    await db.flashcards.insert_one(card_doc)
    card_doc.pop("_id", None)
    card_doc["created_at"] = card_doc["created_at"].isoformat()
    return {"flashcard": card_doc}

# ═══════════════════════════════════════════
# STUDY ROUTES
# ═══════════════════════════════════════════
@api_router.get("/study/start/{subject_id}")
async def start_study(subject_id: str, request: Request, grade: Optional[str] = Query(None)):
    user = await get_current_user(request)
    user_id = user["_id"]
    user_grade = grade or user.get("grade_level")

    query = {"subject_id": subject_id}
    if user_grade:
        query["grade_levels"] = user_grade

    all_cards = await db.flashcards.find(query, {"_id": 0}).to_list(500)
    if not all_cards:
        raise HTTPException(status_code=404, detail="Aucune flashcard pour cette matière et ce niveau")

    card_ids = [c["id"] for c in all_cards]
    progress_list = await db.user_card_progress.find(
        {"user_id": user_id, "card_id": {"$in": card_ids}}, {"_id": 0}
    ).to_list(500)
    progress_map = {p["card_id"]: p for p in progress_list}

    box1, box2, box3 = [], [], []
    for card in all_cards:
        prog = progress_map.get(card["id"])
        if not prog or prog["box"] == 1:
            box1.append(card)
        elif prog["box"] == 2:
            box2.append(card)
        else:
            box3.append(card)

    selected = list(box1)
    if box2:
        selected += random.sample(box2, min(len(box2), max(1, len(box2) // 2)))
    if box3:
        selected += random.sample(box3, min(len(box3), max(1, len(box3) // 4)))
    random.shuffle(selected)
    selected = selected[:15]

    session_cards = []
    for card in selected:
        prog = progress_map.get(card["id"])
        if not prog:
            show_side = "answer"
        else:
            show_side = "question" if prog.get("last_shown_side") == "answer" else "answer"
        session_cards.append({
            "card_id": card["id"], "question": card["question"],
            "answer": card["answer"], "show_side": show_side,
            "box": prog["box"] if prog else 1,
        })
    return {"session_cards": session_cards, "total": len(session_cards)}

@api_router.post("/study/submit")
async def submit_study(input: SubmitStudyInput, request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]

    correct_count = 0
    incorrect_cards = []

    for r in input.results:
        prog = await db.user_card_progress.find_one({"user_id": user_id, "card_id": r.card_id})
        current_box = prog["box"] if prog else 1
        last_shown = prog.get("last_shown_side", "answer") if prog else "answer"
        new_shown = "question" if last_shown == "answer" else "answer"

        if r.is_correct:
            correct_count += 1
            new_box = min(current_box + 1, 3)
        else:
            new_box = 1
            card = await db.flashcards.find_one({"id": r.card_id}, {"_id": 0})
            if card:
                incorrect_cards.append({"question": card["question"], "answer": card["answer"]})

        await db.user_card_progress.update_one(
            {"user_id": user_id, "card_id": r.card_id},
            {"$set": {
                "user_id": user_id, "card_id": r.card_id,
                "subject_id": input.subject_id, "box": new_box,
                "last_shown_side": new_shown,
                "last_reviewed": datetime.now(timezone.utc),
            },
            "$inc": {
                "times_correct": 1 if r.is_correct else 0,
                "times_incorrect": 0 if r.is_correct else 1,
            }},
            upsert=True,
        )

    total = len(input.results)
    percentage = round((correct_count / total) * 100) if total > 0 else 0
    xp_earned = correct_count * 10 + 50
    if percentage == 100:
        xp_earned += 100

    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    new_xp = user_doc.get("xp", 0) + xp_earned
    new_level = (new_xp // 500) + 1

    today = datetime.now(timezone.utc).date()
    last_study = user_doc.get("last_study_date")
    current_streak = user_doc.get("streak_count", 0)
    if last_study:
        last_date = last_study.date() if isinstance(last_study, datetime) else last_study
        diff = (today - last_date).days
        new_streak = current_streak if diff == 0 else (current_streak + 1 if diff == 1 else 1)
    else:
        new_streak = 1

    current_badges = user_doc.get("badges", [])
    badge_ids = [b["id"] for b in current_badges]
    new_badges = []
    BADGE_DEFS = [
        {"id": "first_step", "name": "Premier Pas", "description": "Première session complétée", "icon": "rocket-outline"},
        {"id": "perfectionist", "name": "Perfectionniste", "description": "100% à une session", "icon": "star-outline"},
        {"id": "on_fire_3", "name": "En Feu", "description": "3 jours consécutifs", "icon": "flame-outline"},
        {"id": "marathon_7", "name": "Marathonien", "description": "7 jours consécutifs", "icon": "medal-outline"},
        {"id": "expert", "name": "Expert", "description": "Niveau 5 atteint", "icon": "trophy-outline"},
        {"id": "master", "name": "Maître", "description": "10 cartes en boîte 3", "icon": "school-outline"},
    ]
    if "first_step" not in badge_ids:
        new_badges.append(next(b for b in BADGE_DEFS if b["id"] == "first_step"))
    if percentage == 100 and "perfectionist" not in badge_ids:
        new_badges.append(next(b for b in BADGE_DEFS if b["id"] == "perfectionist"))
    if new_streak >= 3 and "on_fire_3" not in badge_ids:
        new_badges.append(next(b for b in BADGE_DEFS if b["id"] == "on_fire_3"))
    if new_streak >= 7 and "marathon_7" not in badge_ids:
        new_badges.append(next(b for b in BADGE_DEFS if b["id"] == "marathon_7"))
    if new_level >= 5 and "expert" not in badge_ids:
        new_badges.append(next(b for b in BADGE_DEFS if b["id"] == "expert"))
    box3_count = await db.user_card_progress.count_documents({"user_id": user_id, "box": 3})
    if box3_count >= 10 and "master" not in badge_ids:
        new_badges.append(next(b for b in BADGE_DEFS if b["id"] == "master"))

    all_badges = current_badges + new_badges
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"xp": new_xp, "level": new_level, "streak_count": new_streak,
                  "last_study_date": datetime.now(timezone.utc), "badges": all_badges}}
    )

    session_doc = {
        "id": str(ObjectId()), "user_id": user_id, "subject_id": input.subject_id,
        "total_cards": total, "correct_count": correct_count,
        "incorrect_count": total - correct_count, "percentage": percentage,
        "xp_earned": xp_earned, "completed_at": datetime.now(timezone.utc),
    }
    await db.study_sessions.insert_one(session_doc)

    return {
        "total_cards": total, "correct_count": correct_count,
        "incorrect_count": total - correct_count, "percentage": percentage,
        "xp_earned": xp_earned, "new_badges": new_badges,
        "cards_to_review": incorrect_cards, "streak_count": new_streak,
        "new_level": new_level, "total_xp": new_xp,
    }

# ═══════════════════════════════════════════
# PROGRESS ROUTES
# ═══════════════════════════════════════════
@api_router.get("/progress/stats")
async def get_progress_stats(request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]
    sessions = await db.study_sessions.find({"user_id": user_id}, {"_id": 0}).sort("completed_at", -1).to_list(50)
    for s in sessions:
        if isinstance(s.get("completed_at"), datetime):
            s["completed_at"] = s["completed_at"].isoformat()
    box_counts = {}
    for box_num in [1, 2, 3]:
        count = await db.user_card_progress.count_documents({"user_id": user_id, "box": box_num})
        box_counts[f"box_{box_num}"] = count
    return {"sessions": sessions, "box_counts": box_counts, "total_sessions": len(sessions)}

# ═══════════════════════════════════════════
# SUBJECT STATS + LEADERBOARD + THEME
# ═══════════════════════════════════════════
@api_router.get("/progress/subject-stats")
async def get_subject_stats(request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]
    subjects = await db.subjects.find({}, {"_id": 0}).to_list(100)
    result = []
    for subj in subjects:
        sid = subj["id"]
        sessions = await db.study_sessions.find({"user_id": user_id, "subject_id": sid}, {"_id": 0}).to_list(500)
        total_sessions = len(sessions)
        if total_sessions == 0:
            continue
        total_correct = sum(s.get("correct_count", 0) for s in sessions)
        total_cards = sum(s.get("total_cards", 0) for s in sessions)
        avg_pct = round(sum(s.get("percentage", 0) for s in sessions) / total_sessions) if total_sessions else 0
        total_xp = sum(s.get("xp_earned", 0) for s in sessions)
        box_dist = {}
        for b in [1, 2, 3]:
            box_dist[f"box_{b}"] = await db.user_card_progress.count_documents({"user_id": user_id, "subject_id": sid, "box": b})
        total_card_count = await db.flashcards.count_documents({"subject_id": sid})
        mastered = box_dist.get("box_3", 0)
        result.append({
            "subject_id": sid, "name": subj["name"], "color": subj["color"], "icon": subj["icon"],
            "total_sessions": total_sessions, "total_correct": total_correct,
            "total_cards_reviewed": total_cards, "avg_percentage": avg_pct,
            "total_xp": total_xp, "box_distribution": box_dist,
            "total_cards": total_card_count, "mastered": mastered,
            "mastery_pct": round((mastered / total_card_count) * 100) if total_card_count else 0,
        })
    result.sort(key=lambda x: x["total_sessions"], reverse=True)
    return {"subject_stats": result}

@api_router.get("/classes/{class_id}/leaderboard")
async def get_class_leaderboard(class_id: str, request: Request):
    user = await get_current_user(request)
    cls = await db.classes.find_one({"id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    member_ids = [m["user_id"] for m in cls.get("members", [])]
    if user["_id"] not in member_ids:
        raise HTTPException(status_code=403, detail="Accès refusé")
    leaderboard = []
    for member in cls.get("members", []):
        uid = member["user_id"]
        u = await db.users.find_one({"_id": ObjectId(uid)})
        if not u:
            continue
        session_count = await db.study_sessions.count_documents({"user_id": uid})
        sessions = await db.study_sessions.find({"user_id": uid}, {"_id": 0}).to_list(500)
        avg_pct = round(sum(s.get("percentage", 0) for s in sessions) / len(sessions)) if sessions else 0
        leaderboard.append({
            "user_id": uid, "name": u["name"],
            "xp": u.get("xp", 0), "level": u.get("level", 1),
            "streak": u.get("streak_count", 0), "sessions": session_count,
            "avg_score": avg_pct,
        })
    leaderboard.sort(key=lambda x: x["xp"], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    return {"leaderboard": leaderboard}

@api_router.put("/user/theme")
async def update_theme(input: UpdateThemeInput, request: Request):
    user = await get_current_user(request)
    if input.theme not in ["light", "dark"]:
        raise HTTPException(status_code=400, detail="Thème invalide")
    await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"theme": input.theme}})
    return {"theme": input.theme}

# ═══════════════════════════════════════════
# DAILY REWARDS
# ═══════════════════════════════════════════
@api_router.get("/rewards/daily")
async def get_daily_reward(request: Request):
    user = await get_current_user(request)
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

@api_router.post("/rewards/claim")
async def claim_daily_reward(request: Request):
    user = await get_current_user(request)
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

# ═══════════════════════════════════════════
# CLASS ROUTES (Mode Classe)
# ═══════════════════════════════════════════
@api_router.post("/classes")
async def create_class(input: CreateClassInput, request: Request):
    user = await get_current_user(request)
    code = generate_class_code()
    while await db.classes.find_one({"code": code}):
        code = generate_class_code()
    class_doc = {
        "id": str(ObjectId()), "name": input.name.strip(), "code": code,
        "is_private": input.is_private, "locked_grade": input.locked_grade,
        "created_by": user["_id"], "created_by_name": user["name"],
        "members": [{"user_id": user["_id"], "name": user["name"], "role": "admin"}],
        "created_at": datetime.now(timezone.utc),
    }
    await db.classes.insert_one(class_doc)
    class_doc.pop("_id", None)
    class_doc["created_at"] = class_doc["created_at"].isoformat()
    return {"class": class_doc}

@api_router.post("/classes/join")
async def join_class(input: JoinClassInput, request: Request):
    user = await get_current_user(request)
    cls = await db.classes.find_one({"code": input.code.upper().strip()})
    if not cls:
        raise HTTPException(status_code=404, detail="Code de classe invalide")
    member_ids = [m["user_id"] for m in cls.get("members", [])]
    if user["_id"] in member_ids:
        raise HTTPException(status_code=400, detail="Tu fais déjà partie de cette classe")
    # Check grade lock
    if cls.get("locked_grade") and user.get("grade_level") != cls["locked_grade"]:
        raise HTTPException(status_code=403, detail=f"Cette classe est réservée au niveau {cls['locked_grade']}")
    await db.classes.update_one(
        {"code": input.code.upper().strip()},
        {"$push": {"members": {"user_id": user["_id"], "name": user["name"], "role": "member"}}}
    )
    cls = await db.classes.find_one({"code": input.code.upper().strip()}, {"_id": 0})
    if isinstance(cls.get("created_at"), datetime):
        cls["created_at"] = cls["created_at"].isoformat()
    return {"class": cls}

@api_router.get("/classes")
async def get_my_classes(request: Request):
    user = await get_current_user(request)
    classes = await db.classes.find({"members.user_id": user["_id"]}, {"_id": 0}).to_list(100)
    for c in classes:
        if isinstance(c.get("created_at"), datetime):
            c["created_at"] = c["created_at"].isoformat()
        c["member_count"] = len(c.get("members", []))
        deck_count = await db.shared_decks.count_documents({"class_id": c["id"]})
        c["deck_count"] = deck_count
    return {"classes": classes}

@api_router.get("/classes/{class_id}")
async def get_class_detail(class_id: str, request: Request):
    user = await get_current_user(request)
    cls = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if not cls:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    member_ids = [m["user_id"] for m in cls.get("members", [])]
    if user["_id"] not in member_ids:
        raise HTTPException(status_code=403, detail="Tu ne fais pas partie de cette classe")
    if isinstance(cls.get("created_at"), datetime):
        cls["created_at"] = cls["created_at"].isoformat()
    decks = await db.shared_decks.find({"class_id": class_id}, {"_id": 0}).to_list(100)
    for d in decks:
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
    cls["shared_decks"] = decks
    return {"class": cls}

@api_router.post("/classes/{class_id}/share")
async def share_deck(class_id: str, input: ShareDeckInput, request: Request):
    user = await get_current_user(request)
    cls = await db.classes.find_one({"id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    member_ids = [m["user_id"] for m in cls.get("members", [])]
    if user["_id"] not in member_ids:
        raise HTTPException(status_code=403, detail="Tu ne fais pas partie de cette classe")
    cards = await db.flashcards.find({"subject_id": input.subject_id}, {"_id": 0}).to_list(500)
    if not cards:
        raise HTTPException(status_code=404, detail="Aucune carte pour cette matière")
    deck_doc = {
        "id": str(ObjectId()), "class_id": class_id,
        "subject_id": input.subject_id, "name": input.name.strip(),
        "shared_by": user["_id"], "shared_by_name": user["name"],
        "card_ids": [c["id"] for c in cards], "card_count": len(cards),
        "created_at": datetime.now(timezone.utc),
    }
    await db.shared_decks.insert_one(deck_doc)
    deck_doc.pop("_id", None)
    deck_doc["created_at"] = deck_doc["created_at"].isoformat()
    return {"deck": deck_doc}

@api_router.get("/classes/{class_id}/decks/{deck_id}/study")
async def study_shared_deck(class_id: str, deck_id: str, request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]
    cls = await db.classes.find_one({"id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    member_ids = [m["user_id"] for m in cls.get("members", [])]
    if user_id not in member_ids:
        raise HTTPException(status_code=403, detail="Accès refusé")
    deck = await db.shared_decks.find_one({"id": deck_id}, {"_id": 0})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck introuvable")
    cards = await db.flashcards.find({"id": {"$in": deck["card_ids"]}}, {"_id": 0}).to_list(500)
    progress_list = await db.user_card_progress.find(
        {"user_id": user_id, "card_id": {"$in": deck["card_ids"]}}, {"_id": 0}
    ).to_list(500)
    progress_map = {p["card_id"]: p for p in progress_list}

    session_cards = []
    for card in cards:
        prog = progress_map.get(card["id"])
        show_side = "answer" if not prog else ("question" if prog.get("last_shown_side") == "answer" else "answer")
        session_cards.append({
            "card_id": card["id"], "question": card["question"],
            "answer": card["answer"], "show_side": show_side,
            "box": prog["box"] if prog else 1,
        })
    random.shuffle(session_cards)
    return {"session_cards": session_cards[:15], "total": min(len(session_cards), 15), "subject_id": deck["subject_id"]}

# ═══════════════════════════════════════════
# EXPORT / IMPORT ROUTES
# ═══════════════════════════════════════════
@api_router.get("/export/{subject_id}")
async def export_deck(subject_id: str, request: Request):
    user = await get_current_user(request)
    subject = await db.subjects.find_one({"id": subject_id}, {"_id": 0})
    if not subject:
        raise HTTPException(status_code=404, detail="Matière introuvable")
    cards = await db.flashcards.find({"subject_id": subject_id}, {"_id": 0, "created_by": 0, "created_at": 0}).to_list(500)
    for c in cards:
        c.pop("_id", None)
    return {
        "export": {
            "version": "1.0", "subject": subject["name"], "subject_id": subject_id,
            "card_count": len(cards),
            "cards": [{"question": c["question"], "answer": c["answer"],
                       "grade_levels": c.get("grade_levels", GRADE_LEVELS)} for c in cards],
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "exported_by": user["name"],
        }
    }

@api_router.post("/import")
async def import_deck(input: ImportDeckInput, request: Request):
    user = await get_current_user(request)
    subject = await db.subjects.find_one({"id": input.subject_id})
    if not subject:
        raise HTTPException(status_code=404, detail="Matière introuvable")
    imported = 0
    for card_data in input.cards:
        q = card_data.get("question", "").strip()
        a = card_data.get("answer", "").strip()
        if not q or not a:
            continue
        card_id = str(ObjectId())
        gl = card_data.get("grade_levels", list(GRADE_LEVELS))
        await db.flashcards.insert_one({
            "id": card_id, "subject_id": input.subject_id,
            "question": q, "answer": a, "grade_levels": gl,
            "created_by": user["_id"], "created_at": datetime.now(timezone.utc),
        })
        imported += 1
    return {"imported": imported, "subject_id": input.subject_id}

# ═══════════════════════════════════════════
# EXAM REVISION MODE
# ═══════════════════════════════════════════
@api_router.get("/study/exam/{subject_id}")
async def start_exam_revision(subject_id: str, request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]

    # Exam mode: show ALL cards regardless of grade (intensive revision)
    all_cards = await db.flashcards.find({"subject_id": subject_id}, {"_id": 0}).to_list(500)
    if not all_cards:
        raise HTTPException(status_code=404, detail="Aucune flashcard")

    card_ids = [c["id"] for c in all_cards]
    progress_list = await db.user_card_progress.find(
        {"user_id": user_id, "card_id": {"$in": card_ids}}, {"_id": 0}
    ).to_list(500)
    progress_map = {p["card_id"]: p for p in progress_list}

    # Sort: box 1 first (weakest), then box 2, then box 3, then new cards
    def sort_key(card):
        prog = progress_map.get(card["id"])
        if not prog:
            return (0, 0)  # New cards = highest priority
        return (prog["box"], prog.get("times_correct", 0))

    all_cards.sort(key=sort_key)

    session_cards = []
    for card in all_cards[:30]:  # Up to 30 cards for exam mode
        prog = progress_map.get(card["id"])
        show_side = "answer" if not prog else ("question" if prog.get("last_shown_side") == "answer" else "answer")
        session_cards.append({
            "card_id": card["id"], "question": card["question"],
            "answer": card["answer"], "show_side": show_side,
            "box": prog["box"] if prog else 1,
        })

    total_cards = await db.flashcards.count_documents({"subject_id": subject_id})
    mastered = await db.user_card_progress.count_documents({"user_id": user_id, "subject_id": subject_id, "box": 3})

    return {
        "session_cards": session_cards, "total": len(session_cards),
        "total_subject_cards": total_cards, "mastered_cards": mastered,
        "mastery_pct": round((mastered / total_cards) * 100) if total_cards else 0,
    }

# ═══════════════════════════════════════════
# WEEKLY CHALLENGES
# ═══════════════════════════════════════════
@api_router.get("/challenges")
async def get_challenges(request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]
    week_start = get_week_start()
    week_start_dt = datetime(week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc)

    # Get sessions this week
    week_sessions = await db.study_sessions.find(
        {"user_id": user_id, "completed_at": {"$gte": week_start_dt}}, {"_id": 0}
    ).to_list(500)

    # Calculate progress for each challenge
    challenges = []
    for ch in WEEKLY_CHALLENGES:
        progress = 0
        if ch["type"] == "sessions":
            progress = len(week_sessions)
        elif ch["type"] == "perfect":
            progress = sum(1 for s in week_sessions if s.get("percentage") == 100)
        elif ch["type"] == "subjects":
            progress = len(set(s.get("subject_id") for s in week_sessions))
        elif ch["type"] == "master":
            progress = await db.user_card_progress.count_documents({
                "user_id": user_id, "box": 3,
                "last_reviewed": {"$gte": week_start_dt}
            })

        completed = progress >= ch["target"]
        # Check if already claimed
        claimed = await db.challenge_claims.find_one({
            "user_id": user_id, "challenge_id": ch["id"],
            "week_start": week_start.isoformat(),
        })

        challenges.append({
            **ch, "progress": min(progress, ch["target"]),
            "completed": completed, "claimed": bool(claimed),
        })

    return {"challenges": challenges, "week_start": week_start.isoformat()}

@api_router.post("/challenges/{challenge_id}/claim")
async def claim_challenge(challenge_id: str, request: Request):
    user = await get_current_user(request)
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

    # Verify completion
    week_start_dt = datetime(week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc)
    week_sessions = await db.study_sessions.find(
        {"user_id": user_id, "completed_at": {"$gte": week_start_dt}}, {"_id": 0}
    ).to_list(500)

    progress = 0
    if ch["type"] == "sessions":
        progress = len(week_sessions)
    elif ch["type"] == "perfect":
        progress = sum(1 for s in week_sessions if s.get("percentage") == 100)
    elif ch["type"] == "subjects":
        progress = len(set(s.get("subject_id") for s in week_sessions))
    elif ch["type"] == "master":
        progress = await db.user_card_progress.count_documents({
            "user_id": user_id, "box": 3, "last_reviewed": {"$gte": week_start_dt}
        })

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

# ═══════════════════════════════════════════
# SOCIAL SHARING
# ═══════════════════════════════════════════
@api_router.get("/share/profile")
async def get_share_profile(request: Request):
    user = await get_current_user(request)
    user_doc = await db.users.find_one({"_id": ObjectId(user["_id"])})
    session_count = await db.study_sessions.count_documents({"user_id": user["_id"]})
    box3 = await db.user_card_progress.count_documents({"user_id": user["_id"], "box": 3})
    text = (
        f"📚 FlashCards — Mon profil\n"
        f"👤 {user_doc['name']}\n"
        f"⭐ {user_doc.get('xp', 0)} XP • Niveau {user_doc.get('level', 1)}\n"
        f"🔥 {user_doc.get('streak_count', 0)} jours de streak\n"
        f"📖 {session_count} sessions complétées\n"
        f"🏆 {len(user_doc.get('badges', []))} badges • {box3} cartes maîtrisées\n"
        f"#FlashCards #Révisions #Éducation"
    )
    return {"share_text": text}

@api_router.post("/share/session")
async def get_share_session(request: Request):
    body = await request.json()
    pct = body.get("percentage", 0)
    correct = body.get("correct", 0)
    total = body.get("total", 0)
    xp = body.get("xp_earned", 0)
    emoji = "🏆" if pct == 100 else ("🎉" if pct >= 80 else ("👍" if pct >= 50 else "💪"))
    text = (
        f"{emoji} FlashCards — Résultat\n"
        f"📊 Score : {pct}% ({correct}/{total})\n"
        f"⭐ +{xp} XP gagnés\n"
        f"#FlashCards #Révisions"
    )
    return {"share_text": text}

# ═══════════════════════════════════════════
# AI FLASHCARD GENERATION (Claude Sonnet)
# ═══════════════════════════════════════════
class AIGenerateInput(BaseModel):
    subject_id: str
    text: str
    count: int = 5

@api_router.post("/ai/generate")
async def ai_generate_flashcards(input: AIGenerateInput, request: Request):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json as json_mod
    import uuid

    subject = await db.subjects.find_one({"id": input.subject_id}, {"_id": 0})
    subject_name = subject["name"] if subject else input.subject_id

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Clé IA non configurée")

    chat = LlmChat(
        api_key=api_key,
        session_id=f"flashcard-gen-{uuid.uuid4().hex[:8]}",
        system_message=(
            "Tu es un assistant pédagogique expert pour les élèves français de la 6ème à la Terminale. "
            "Tu génères des flashcards éducatives au format JSON. "
            "Chaque flashcard a un 'question' (terme/concept) et une 'answer' (définition concise). "
            "Réponds UNIQUEMENT avec un tableau JSON valide, sans texte autour."
        )
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")

    prompt = (
        f"Matière: {subject_name}\n\n"
        f"À partir du texte suivant, génère exactement {input.count} flashcards éducatives.\n"
        f"Format: un tableau JSON [{{'question': '...', 'answer': '...'}}]\n\n"
        f"Texte:\n{input.text[:3000]}"
    )

    try:
        response = await chat.send_message(UserMessage(text=prompt))
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        cards_data = json_mod.loads(response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur IA: {str(e)}")

    saved = []
    user_grade = user.get("grade_level")
    gl = [user_grade] if user_grade else list(GRADE_LEVELS)
    for card_data in cards_data[:input.count]:
        q = card_data.get("question", "").strip()
        a = card_data.get("answer", "").strip()
        if not q or not a:
            continue
        card_id = str(ObjectId())
        await db.flashcards.insert_one({
            "id": card_id, "subject_id": input.subject_id,
            "question": q, "answer": a, "grade_levels": gl,
            "created_by": user["_id"], "created_at": datetime.now(timezone.utc),
        })
        saved.append({"id": card_id, "question": q, "answer": a})
    return {"generated": len(saved), "cards": saved}

# ═══════════════════════════════════════════
# SYNC STATUS
# ═══════════════════════════════════════════
@api_router.get("/sync/status")
async def get_sync_status(request: Request):
    user = await get_current_user(request)
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

# ═══════════════════════════════════════════
# SEED DATA
# ═══════════════════════════════════════════
SUBJECTS_SEED = [
    {"id": "maths", "name": "Maths", "icon": "calculator-outline", "color": "#2563EB", "description": "Algèbre, géométrie, fonctions"},
    {"id": "francais", "name": "Français", "icon": "book-outline", "color": "#E11D48", "description": "Littérature, grammaire, figures de style"},
    {"id": "histoire_geo", "name": "Histoire-Géo", "icon": "earth-outline", "color": "#D97706", "description": "Dates clés, civilisations, géographie"},
    {"id": "svt", "name": "SVT", "icon": "leaf-outline", "color": "#16A34A", "description": "Biologie, écologie, géologie"},
    {"id": "physique_chimie", "name": "Physique-Chimie", "icon": "flask-outline", "color": "#0891B2", "description": "Lois physiques, réactions chimiques"},
    {"id": "anglais", "name": "Anglais", "icon": "language-outline", "color": "#EA580C", "description": "Grammaire, vocabulaire, expressions"},
    {"id": "philosophie", "name": "Philosophie", "icon": "bulb-outline", "color": "#475569", "description": "Courants, penseurs, concepts"},
    {"id": "ses", "name": "SES", "icon": "trending-up-outline", "color": "#059669", "description": "Économie, sociologie, politique"},
    {"id": "espagnol", "name": "Espagnol", "icon": "sunny-outline", "color": "#DC2626", "description": "Grammaire, conjugaison, vocabulaire"},
]

ALL_GRADES = GRADE_LEVELS
COLLEGE = ["6eme", "5eme", "4eme", "3eme"]
LYCEE = ["2nde", "1ere", "terminale"]

FLASHCARDS_SEED = [
    # Maths
    {"id": "m1", "subject_id": "maths", "question": "Théorème de Pythagore", "answer": "Dans un triangle rectangle, a² + b² = c²", "grade_levels": COLLEGE},
    {"id": "m2", "subject_id": "maths", "question": "Identité remarquable (a+b)²", "answer": "(a+b)² = a² + 2ab + b²", "grade_levels": ["3eme", "2nde", "1ere"]},
    {"id": "m3", "subject_id": "maths", "question": "Aire d'un cercle", "answer": "A = πr² où r est le rayon", "grade_levels": COLLEGE},
    {"id": "m4", "subject_id": "maths", "question": "PGCD", "answer": "Plus Grand Commun Diviseur de deux entiers", "grade_levels": ["5eme", "4eme", "3eme"]},
    {"id": "m5", "subject_id": "maths", "question": "Fonction affine", "answer": "f(x) = ax + b, droite de pente a", "grade_levels": ["3eme", "2nde"]},
    # Français
    {"id": "f1", "subject_id": "francais", "question": "Métaphore", "answer": "Comparaison sans outil de comparaison", "grade_levels": ALL_GRADES},
    {"id": "f2", "subject_id": "francais", "question": "Oxymore", "answer": "Association de deux termes contraires. Ex: 'obscure clarté'", "grade_levels": ["3eme"] + LYCEE},
    {"id": "f3", "subject_id": "francais", "question": "Alexandrin", "answer": "Vers de 12 syllabes", "grade_levels": ALL_GRADES},
    {"id": "f4", "subject_id": "francais", "question": "Champ lexical", "answer": "Ensemble de mots d'un même thème", "grade_levels": ALL_GRADES},
    {"id": "f5", "subject_id": "francais", "question": "Hyperbole", "answer": "Exagération pour frapper l'esprit", "grade_levels": ALL_GRADES},
    # Histoire-Géo
    {"id": "h1", "subject_id": "histoire_geo", "question": "Révolution française", "answer": "1789 — Fin de la monarchie absolue", "grade_levels": ALL_GRADES},
    {"id": "h2", "subject_id": "histoire_geo", "question": "Première Guerre mondiale", "answer": "1914-1918 — Conflit mondial, 10M de morts", "grade_levels": ["3eme"] + LYCEE},
    {"id": "h3", "subject_id": "histoire_geo", "question": "Débarquement en Normandie", "answer": "6 juin 1944 (Jour J)", "grade_levels": ["3eme"] + LYCEE},
    {"id": "h4", "subject_id": "histoire_geo", "question": "Les Trente Glorieuses", "answer": "Croissance économique 1945-1975", "grade_levels": LYCEE},
    {"id": "h5", "subject_id": "histoire_geo", "question": "La mondialisation", "answer": "Intégration mondiale des marchés et sociétés", "grade_levels": LYCEE},
    # SVT
    {"id": "s1", "subject_id": "svt", "question": "Photosynthèse", "answer": "CO₂ + eau → glucose + O₂ (lumière)", "grade_levels": ALL_GRADES},
    {"id": "s2", "subject_id": "svt", "question": "ADN", "answer": "Molécule de l'information génétique, double hélice", "grade_levels": ["3eme"] + LYCEE},
    {"id": "s3", "subject_id": "svt", "question": "Mitose", "answer": "Division cellulaire → 2 cellules identiques", "grade_levels": ["3eme"] + LYCEE},
    {"id": "s4", "subject_id": "svt", "question": "Tectonique des plaques", "answer": "Mouvement des plaques lithosphériques", "grade_levels": COLLEGE},
    {"id": "s5", "subject_id": "svt", "question": "Écosystème", "answer": "Communauté vivante + environnement physique", "grade_levels": ALL_GRADES},
    # Physique-Chimie
    {"id": "p1", "subject_id": "physique_chimie", "question": "Loi d'Ohm", "answer": "U = R × I", "grade_levels": ["4eme", "3eme", "2nde"]},
    {"id": "p2", "subject_id": "physique_chimie", "question": "Énergie cinétique", "answer": "Ec = ½mv²", "grade_levels": LYCEE},
    {"id": "p3", "subject_id": "physique_chimie", "question": "Atome", "answer": "Noyau (protons+neutrons) + électrons", "grade_levels": ALL_GRADES},
    {"id": "p4", "subject_id": "physique_chimie", "question": "Vitesse de la lumière", "answer": "c ≈ 3×10⁸ m/s", "grade_levels": ["4eme", "3eme"] + LYCEE},
    {"id": "p5", "subject_id": "physique_chimie", "question": "pH", "answer": "<7 acide, =7 neutre, >7 basique", "grade_levels": ["3eme"] + LYCEE},
    # Anglais
    {"id": "a1", "subject_id": "anglais", "question": "Present Perfect", "answer": "Have/Has + past participle", "grade_levels": ALL_GRADES},
    {"id": "a2", "subject_id": "anglais", "question": "Conditional (2nd)", "answer": "If + past simple, would + verb", "grade_levels": ["3eme"] + LYCEE},
    {"id": "a3", "subject_id": "anglais", "question": "To look forward to", "answer": "Attendre avec impatience", "grade_levels": ALL_GRADES},
    {"id": "a4", "subject_id": "anglais", "question": "Passive voice", "answer": "Subject + be + past participle", "grade_levels": ["4eme", "3eme"] + LYCEE},
    {"id": "a5", "subject_id": "anglais", "question": "Since vs For", "answer": "Since = point. For = durée", "grade_levels": ALL_GRADES},
    # Philosophie (Terminale only)
    {"id": "ph1", "subject_id": "philosophie", "question": "Cogito ergo sum", "answer": "Je pense donc je suis — Descartes", "grade_levels": ["terminale"]},
    {"id": "ph2", "subject_id": "philosophie", "question": "L'allégorie de la caverne", "answer": "Platon — Ombres vs réalité", "grade_levels": ["terminale"]},
    {"id": "ph3", "subject_id": "philosophie", "question": "L'impératif catégorique", "answer": "Kant — Maxime érigeable en loi universelle", "grade_levels": ["terminale"]},
    {"id": "ph4", "subject_id": "philosophie", "question": "Le contrat social", "answer": "Rousseau — Liberté contre protection", "grade_levels": ["terminale"]},
    {"id": "ph5", "subject_id": "philosophie", "question": "L'existentialisme", "answer": "Sartre — L'existence précède l'essence", "grade_levels": ["terminale"]},
    # SES
    {"id": "se1", "subject_id": "ses", "question": "PIB", "answer": "Produit Intérieur Brut — Richesse annuelle", "grade_levels": ["2nde", "1ere", "terminale"]},
    {"id": "se2", "subject_id": "ses", "question": "Inflation", "answer": "Hausse générale et durable des prix", "grade_levels": ["2nde", "1ere", "terminale"]},
    {"id": "se3", "subject_id": "ses", "question": "Loi offre/demande", "answer": "Demande↑→prix↑, Offre↑→prix↓", "grade_levels": ["2nde", "1ere", "terminale"]},
    {"id": "se4", "subject_id": "ses", "question": "Mobilité sociale", "answer": "Changement de position entre générations", "grade_levels": ["1ere", "terminale"]},
    {"id": "se5", "subject_id": "ses", "question": "Mondialisation économique", "answer": "Intégration des économies nationales", "grade_levels": ["terminale"]},
    # Espagnol
    {"id": "es1", "subject_id": "espagnol", "question": "Ser vs Estar", "answer": "Ser=permanent, Estar=temporaire", "grade_levels": ALL_GRADES},
    {"id": "es2", "subject_id": "espagnol", "question": "Pretérito indefinido", "answer": "Passé simple: hablé, hablaste, habló...", "grade_levels": ["4eme", "3eme"] + LYCEE},
    {"id": "es3", "subject_id": "espagnol", "question": "Gustar", "answer": "Me gusta/gustan = ça me plaît", "grade_levels": ALL_GRADES},
    {"id": "es4", "subject_id": "espagnol", "question": "Subjuntivo", "answer": "Mode du doute/souhait", "grade_levels": LYCEE},
    {"id": "es5", "subject_id": "espagnol", "question": "Por vs Para", "answer": "Por=cause/durée, Para=but/destination", "grade_levels": ["3eme"] + LYCEE},
]

async def seed_data():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@flashcards.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "email": admin_email, "password_hash": hash_password(admin_password),
            "name": "Admin", "role": "admin", "xp": 0, "level": 1,
            "streak_count": 0, "last_study_date": None, "badges": [],
            "grade_level": None, "notification_enabled": True, "notification_hour": 18,
            "created_at": datetime.now(timezone.utc),
        })
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})

    for subj in SUBJECTS_SEED:
        await db.subjects.update_one({"id": subj["id"]}, {"$set": subj}, upsert=True)
    for card in FLASHCARDS_SEED:
        card_doc = {**card, "created_by": None, "created_at": datetime.now(timezone.utc)}
        await db.flashcards.update_one({"id": card["id"]}, {"$set": card_doc}, upsert=True)

    await db.users.create_index("email", unique=True)
    await db.flashcards.create_index("subject_id")
    await db.flashcards.create_index("grade_levels")
    await db.user_card_progress.create_index([("user_id", 1), ("card_id", 1)], unique=True)
    await db.study_sessions.create_index("user_id")
    await db.classes.create_index("code", unique=True)
    await db.classes.create_index("members.user_id")
    await db.shared_decks.create_index("class_id")
    await db.challenge_claims.create_index([("user_id", 1), ("challenge_id", 1), ("week_start", 1)], unique=True)
    logger.info("Seed data loaded successfully")

@app.on_event("startup")
async def startup():
    await seed_data()

@app.on_event("shutdown")
async def shutdown():
    client.close()

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
