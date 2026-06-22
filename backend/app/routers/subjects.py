from typing import Optional

from fastapi import APIRouter, Query, Depends

from app.config import GRADE_LEVELS, grades_up_to
from app.db import db
from app.security import get_current_user

router = APIRouter()


@router.get("/subjects")
async def get_subjects(grade: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    user_grade = grade or user.get("grade_level")
    subjects = await db.subjects.find({}, {"_id": 0}).to_list(100)
    for s in subjects:
        query = {"subject_id": s["id"]}
        if user_grade:
            # Show cards whose min_grade <= user's grade (i.e. any grade in
            # grades_up_to is in card's grade_levels)
            applicable = grades_up_to(user_grade)
            query["grade_levels"] = {"$in": applicable}
        count = await db.flashcards.count_documents(query)
        s["card_count"] = count
    if user_grade:
        subjects = [s for s in subjects if s["card_count"] > 0]
    return {"subjects": subjects, "grade_levels": GRADE_LEVELS}
