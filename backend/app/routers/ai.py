import os
import json as json_mod
import uuid
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.config import GRADE_LEVELS
from app.db import db
from app.schemas import AIGenerateInput
from app.security import get_current_user

router = APIRouter()


@router.post("/ai/generate")
async def ai_generate_flashcards(input: AIGenerateInput, user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage

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
