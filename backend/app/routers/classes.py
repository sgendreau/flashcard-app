import random
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.db import db
from app.schemas import CreateClassInput, JoinClassInput, ShareDeckInput
from app.security import get_current_user
from app.helpers import generate_class_code

router = APIRouter()


@router.post("/classes")
async def create_class(input: CreateClassInput, user: dict = Depends(get_current_user)):
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


@router.post("/classes/join")
async def join_class(input: JoinClassInput, user: dict = Depends(get_current_user)):
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


@router.get("/classes")
async def get_my_classes(user: dict = Depends(get_current_user)):
    classes = await db.classes.find({"members.user_id": user["_id"]}, {"_id": 0}).to_list(100)
    for c in classes:
        if isinstance(c.get("created_at"), datetime):
            c["created_at"] = c["created_at"].isoformat()
        c["member_count"] = len(c.get("members", []))
        deck_count = await db.shared_decks.count_documents({"class_id": c["id"]})
        c["deck_count"] = deck_count
    return {"classes": classes}


@router.get("/classes/{class_id}")
async def get_class_detail(class_id: str, user: dict = Depends(get_current_user)):
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


@router.get("/classes/{class_id}/leaderboard")
async def get_class_leaderboard(class_id: str, user: dict = Depends(get_current_user)):
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


@router.post("/classes/{class_id}/share")
async def share_deck(class_id: str, input: ShareDeckInput, user: dict = Depends(get_current_user)):
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


@router.get("/classes/{class_id}/decks/{deck_id}/study")
async def study_shared_deck(class_id: str, deck_id: str, user: dict = Depends(get_current_user)):
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
