from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.config import GRADE_LEVELS
from app.db import db
from app.schemas import CreateFlashcardInput, ImportDeckInput
from app.security import get_current_user

router = APIRouter()


@router.get("/flashcards/{subject_id}")
async def get_flashcards(subject_id: str, user: dict = Depends(get_current_user)):
    cards = await db.flashcards.find({"subject_id": subject_id}, {"_id": 0}).to_list(500)
    return {"flashcards": cards}


@router.post("/flashcards")
async def create_flashcard(input: CreateFlashcardInput, user: dict = Depends(get_current_user)):
    card_id = str(ObjectId())
    gl = input.grade_levels if input.grade_levels else list(GRADE_LEVELS)
    card_doc = {
        "id": card_id, "subject_id": input.subject_id,
        "question": input.question.strip(), "answer": input.answer.strip(),
        "grade_levels": gl,
        "created_by": user["_id"], "created_at": datetime.now(timezone.utc),
        "source": "perso",
    }
    await db.flashcards.insert_one(card_doc)
    card_doc.pop("_id", None)
    card_doc["created_at"] = card_doc["created_at"].isoformat()
    return {"flashcard": card_doc}


# ─── EXPORT / IMPORT ───
@router.get("/export/{subject_id}")
async def export_deck(subject_id: str, user: dict = Depends(get_current_user)):
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


@router.post("/import")
async def import_deck(input: ImportDeckInput, user: dict = Depends(get_current_user)):
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
