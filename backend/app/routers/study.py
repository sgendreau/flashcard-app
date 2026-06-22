import random
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException, Depends

from app.config import BADGE_DEFS, grades_up_to
from app.db import db
from app.schemas import SubmitStudyInput
from app.security import get_current_user

router = APIRouter()


@router.get("/study/start/{subject_id}")
async def start_study(subject_id: str, grade: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    user_id = user["_id"]
    user_grade = grade or user.get("grade_level")

    query = {"subject_id": subject_id}
    if user_grade:
        applicable = grades_up_to(user_grade)
        query["grade_levels"] = {"$in": applicable}

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


@router.post("/study/submit")
async def submit_study(input: SubmitStudyInput, user: dict = Depends(get_current_user)):
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
            }, "$inc": {
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


@router.get("/study/exam/{subject_id}")
async def start_exam_revision(subject_id: str, user: dict = Depends(get_current_user)):
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


# ─── PROGRESS ───
@router.get("/progress/stats")
async def get_progress_stats(user: dict = Depends(get_current_user)):
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


@router.get("/progress/subject-stats")
async def get_subject_stats(user: dict = Depends(get_current_user)):
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
