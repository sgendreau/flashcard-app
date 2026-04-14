from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, Request, HTTPException
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import bcrypt
import jwt
import secrets
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from typing import List, Optional
import random

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_ALGORITHM = "HS256"

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

# Pydantic Models
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

# App setup
app = FastAPI()
api_router = APIRouter(prefix="/api")

# ─── AUTH ROUTES ───
@api_router.post("/auth/register")
async def register(input: RegisterInput):
    email = input.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    user_doc = {
        "email": email,
        "password_hash": hash_password(input.password),
        "name": input.name.strip(),
        "role": "student",
        "xp": 0,
        "level": 1,
        "streak_count": 0,
        "last_study_date": None,
        "badges": [],
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    return {
        "user": {"id": user_id, "email": email, "name": input.name.strip(), "xp": 0, "level": 1, "streak_count": 0, "badges": [], "role": "student"},
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

@api_router.post("/auth/login")
async def login(input: LoginInput):
    email = input.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if not verify_password(input.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    return {
        "user": {
            "id": user_id, "email": email, "name": user["name"],
            "xp": user.get("xp", 0), "level": user.get("level", 1),
            "streak_count": user.get("streak_count", 0),
            "badges": user.get("badges", []), "role": user.get("role", "student"),
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return {"user": {
        "id": user["_id"], "email": user["email"], "name": user["name"],
        "xp": user.get("xp", 0), "level": user.get("level", 1),
        "streak_count": user.get("streak_count", 0),
        "badges": user.get("badges", []), "role": user.get("role", "student"),
    }}

@api_router.post("/auth/logout")
async def logout():
    return {"message": "Déconnexion réussie"}

# ─── SUBJECTS ROUTES ───
@api_router.get("/subjects")
async def get_subjects(request: Request):
    await get_current_user(request)
    subjects = await db.subjects.find({}, {"_id": 0}).to_list(100)
    # Add card counts
    for s in subjects:
        count = await db.flashcards.count_documents({"subject_id": s["id"]})
        s["card_count"] = count
    return {"subjects": subjects}

# ─── FLASHCARDS ROUTES ───
@api_router.get("/flashcards/{subject_id}")
async def get_flashcards(subject_id: str, request: Request):
    await get_current_user(request)
    cards = await db.flashcards.find({"subject_id": subject_id}, {"_id": 0}).to_list(500)
    return {"flashcards": cards}

@api_router.post("/flashcards")
async def create_flashcard(input: CreateFlashcardInput, request: Request):
    user = await get_current_user(request)
    card_id = str(ObjectId())
    card_doc = {
        "id": card_id,
        "subject_id": input.subject_id,
        "question": input.question.strip(),
        "answer": input.answer.strip(),
        "created_by": user["_id"],
        "created_at": datetime.now(timezone.utc),
    }
    await db.flashcards.insert_one(card_doc)
    card_doc.pop("_id", None)
    card_doc["created_at"] = card_doc["created_at"].isoformat()
    return {"flashcard": card_doc}

# ─── STUDY ROUTES ───
@api_router.get("/study/start/{subject_id}")
async def start_study(subject_id: str, request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]

    # Get all cards for subject
    all_cards = await db.flashcards.find({"subject_id": subject_id}, {"_id": 0}).to_list(500)
    if not all_cards:
        raise HTTPException(status_code=404, detail="Aucune flashcard pour cette matière")

    # Get user progress for these cards
    card_ids = [c["id"] for c in all_cards]
    progress_list = await db.user_card_progress.find(
        {"user_id": user_id, "card_id": {"$in": card_ids}}, {"_id": 0}
    ).to_list(500)
    progress_map = {p["card_id"]: p for p in progress_list}

    # Categorize by box
    box1, box2, box3 = [], [], []
    for card in all_cards:
        prog = progress_map.get(card["id"])
        if not prog:
            box1.append(card)
        elif prog["box"] == 1:
            box1.append(card)
        elif prog["box"] == 2:
            box2.append(card)
        else:
            box3.append(card)

    # Select cards: all box1, 50% box2, 25% box3, cap at 15
    selected = list(box1)
    if box2:
        selected += random.sample(box2, min(len(box2), max(1, len(box2) // 2)))
    if box3:
        selected += random.sample(box3, min(len(box3), max(1, len(box3) // 4)))
    random.shuffle(selected)
    selected = selected[:15]

    # Determine which side to show for each card
    session_cards = []
    for card in selected:
        prog = progress_map.get(card["id"])
        if not prog:
            show_side = "answer"  # First time: show definition
        else:
            show_side = "question" if prog.get("last_shown_side") == "answer" else "answer"

        session_cards.append({
            "card_id": card["id"],
            "question": card["question"],
            "answer": card["answer"],
            "show_side": show_side,
            "box": prog["box"] if prog else 1,
        })

    return {"session_cards": session_cards, "total": len(session_cards)}

@api_router.post("/study/submit")
async def submit_study(input: SubmitStudyInput, request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]

    correct_count = 0
    incorrect_cards = []
    cards_moved_to_box3 = 0

    for r in input.results:
        # Get current progress
        prog = await db.user_card_progress.find_one({"user_id": user_id, "card_id": r.card_id})

        current_box = prog["box"] if prog else 1
        last_shown = prog.get("last_shown_side", "answer") if prog else "answer"
        new_shown = "question" if last_shown == "answer" else "answer"

        if r.is_correct:
            correct_count += 1
            new_box = min(current_box + 1, 3)
        else:
            new_box = 1
            # Get card info for review list
            card = await db.flashcards.find_one({"id": r.card_id}, {"_id": 0})
            if card:
                incorrect_cards.append({"question": card["question"], "answer": card["answer"]})

        if new_box == 3 and current_box < 3:
            cards_moved_to_box3 += 1

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

    # XP calculation
    xp_earned = correct_count * 10 + 50  # per correct + session bonus
    if percentage == 100:
        xp_earned += 100  # perfect bonus

    # Update user XP
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    new_xp = user_doc.get("xp", 0) + xp_earned
    new_level = (new_xp // 500) + 1

    # Streak calculation
    today = datetime.now(timezone.utc).date()
    last_study = user_doc.get("last_study_date")
    current_streak = user_doc.get("streak_count", 0)

    if last_study:
        if isinstance(last_study, datetime):
            last_date = last_study.date()
        else:
            last_date = last_study
        diff = (today - last_date).days
        if diff == 0:
            new_streak = current_streak  # Same day
        elif diff == 1:
            new_streak = current_streak + 1  # Consecutive
        else:
            new_streak = 1  # Reset
    else:
        new_streak = 1

    # Badge checking
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

    # Check badges
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

    # Count total box3 cards
    box3_count = await db.user_card_progress.count_documents({"user_id": user_id, "box": 3})
    if box3_count >= 10 and "master" not in badge_ids:
        new_badges.append(next(b for b in BADGE_DEFS if b["id"] == "master"))

    all_badges = current_badges + new_badges

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "xp": new_xp, "level": new_level,
            "streak_count": new_streak,
            "last_study_date": datetime.now(timezone.utc),
            "badges": all_badges,
        }}
    )

    # Save session
    session_doc = {
        "id": str(ObjectId()),
        "user_id": user_id,
        "subject_id": input.subject_id,
        "total_cards": total,
        "correct_count": correct_count,
        "incorrect_count": total - correct_count,
        "percentage": percentage,
        "xp_earned": xp_earned,
        "completed_at": datetime.now(timezone.utc),
    }
    await db.study_sessions.insert_one(session_doc)

    return {
        "total_cards": total,
        "correct_count": correct_count,
        "incorrect_count": total - correct_count,
        "percentage": percentage,
        "xp_earned": xp_earned,
        "new_badges": new_badges,
        "cards_to_review": incorrect_cards,
        "streak_count": new_streak,
        "new_level": new_level,
        "total_xp": new_xp,
    }

# ─── PROGRESS ROUTES ───
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

    return {
        "sessions": sessions,
        "box_counts": box_counts,
        "total_sessions": len(sessions),
    }

# ─── SEED DATA ───
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

FLASHCARDS_SEED = [
    # Maths
    {"id": "m1", "subject_id": "maths", "question": "Théorème de Pythagore", "answer": "Dans un triangle rectangle, le carré de l'hypoténuse est égal à la somme des carrés des deux autres côtés : a² + b² = c²"},
    {"id": "m2", "subject_id": "maths", "question": "Identité remarquable (a+b)²", "answer": "(a+b)² = a² + 2ab + b²"},
    {"id": "m3", "subject_id": "maths", "question": "Aire d'un cercle", "answer": "A = πr² où r est le rayon du cercle"},
    {"id": "m4", "subject_id": "maths", "question": "PGCD", "answer": "Plus Grand Commun Diviseur : le plus grand nombre qui divise deux nombres entiers"},
    {"id": "m5", "subject_id": "maths", "question": "Fonction affine", "answer": "f(x) = ax + b, représentée par une droite de pente a et d'ordonnée à l'origine b"},
    # Français
    {"id": "f1", "subject_id": "francais", "question": "Métaphore", "answer": "Figure de style qui établit une comparaison sans outil de comparaison (comme, tel que...)"},
    {"id": "f2", "subject_id": "francais", "question": "Oxymore", "answer": "Figure de style qui associe deux termes de sens contraires. Ex : 'cette obscure clarté'"},
    {"id": "f3", "subject_id": "francais", "question": "Alexandrin", "answer": "Vers de 12 syllabes, très utilisé dans la poésie classique française"},
    {"id": "f4", "subject_id": "francais", "question": "Champ lexical", "answer": "Ensemble de mots se rapportant à un même thème ou une même notion"},
    {"id": "f5", "subject_id": "francais", "question": "Hyperbole", "answer": "Figure de style consistant à exagérer l'expression pour frapper l'esprit"},
    # Histoire-Géo
    {"id": "h1", "subject_id": "histoire_geo", "question": "Révolution française", "answer": "1789 — Renversement de la monarchie absolue, Déclaration des droits de l'homme et du citoyen"},
    {"id": "h2", "subject_id": "histoire_geo", "question": "Première Guerre mondiale", "answer": "1914-1918 — Conflit mondial opposant les Alliés aux Empires centraux, environ 10 millions de morts"},
    {"id": "h3", "subject_id": "histoire_geo", "question": "Débarquement en Normandie", "answer": "6 juin 1944 (Jour J) — Opération militaire alliée sur les plages de Normandie"},
    {"id": "h4", "subject_id": "histoire_geo", "question": "Les Trente Glorieuses", "answer": "Période de forte croissance économique en France de 1945 à 1975"},
    {"id": "h5", "subject_id": "histoire_geo", "question": "La mondialisation", "answer": "Processus d'intégration des marchés et des sociétés à l'échelle mondiale"},
    # SVT
    {"id": "s1", "subject_id": "svt", "question": "Photosynthèse", "answer": "Processus par lequel les plantes convertissent le CO₂ et l'eau en glucose et O₂ grâce à la lumière"},
    {"id": "s2", "subject_id": "svt", "question": "ADN", "answer": "Acide DésoxyriboNucléique — molécule portant l'information génétique, en forme de double hélice"},
    {"id": "s3", "subject_id": "svt", "question": "Mitose", "answer": "Division cellulaire qui produit deux cellules filles identiques à la cellule mère"},
    {"id": "s4", "subject_id": "svt", "question": "Tectonique des plaques", "answer": "Théorie expliquant le mouvement des plaques lithosphériques à la surface de la Terre"},
    {"id": "s5", "subject_id": "svt", "question": "Écosystème", "answer": "Ensemble formé par une communauté d'êtres vivants et leur environnement physique"},
    # Physique-Chimie
    {"id": "p1", "subject_id": "physique_chimie", "question": "Loi d'Ohm", "answer": "U = R × I — la tension (U) est égale au produit de la résistance (R) par l'intensité (I)"},
    {"id": "p2", "subject_id": "physique_chimie", "question": "Énergie cinétique", "answer": "Ec = ½mv² — énergie liée au mouvement d'un objet"},
    {"id": "p3", "subject_id": "physique_chimie", "question": "Atome", "answer": "Plus petite unité de matière, composé d'un noyau (protons + neutrons) et d'électrons"},
    {"id": "p4", "subject_id": "physique_chimie", "question": "Vitesse de la lumière", "answer": "c ≈ 3 × 10⁸ m/s dans le vide"},
    {"id": "p5", "subject_id": "physique_chimie", "question": "pH", "answer": "Mesure de l'acidité : pH < 7 = acide, pH = 7 = neutre, pH > 7 = basique"},
    # Anglais
    {"id": "a1", "subject_id": "anglais", "question": "Present Perfect", "answer": "Have/Has + past participle. Actions passées avec lien au présent. Ex: I have visited Paris"},
    {"id": "a2", "subject_id": "anglais", "question": "Conditional (2nd)", "answer": "If + past simple, would + verb. Condition irréelle. Ex: If I were rich, I would travel"},
    {"id": "a3", "subject_id": "anglais", "question": "To look forward to", "answer": "Attendre avec impatience. Ex: I look forward to meeting you"},
    {"id": "a4", "subject_id": "anglais", "question": "Passive voice", "answer": "Subject + be + past participle. Le sujet subit l'action. Ex: The cake was eaten"},
    {"id": "a5", "subject_id": "anglais", "question": "Since vs For", "answer": "Since = point dans le temps. For = durée. I've lived here since 2020 / for 5 years"},
    # Philosophie
    {"id": "ph1", "subject_id": "philosophie", "question": "Cogito ergo sum", "answer": "Je pense donc je suis — René Descartes. Le doute prouve l'existence du sujet pensant"},
    {"id": "ph2", "subject_id": "philosophie", "question": "L'allégorie de la caverne", "answer": "Platon — Les hommes enchaînés ne voient que des ombres. Métaphore de l'accès à la vérité"},
    {"id": "ph3", "subject_id": "philosophie", "question": "L'impératif catégorique", "answer": "Kant — Agis de telle sorte que la maxime de ton action puisse être érigée en loi universelle"},
    {"id": "ph4", "subject_id": "philosophie", "question": "Le contrat social", "answer": "Rousseau — Les individus renoncent à une liberté naturelle en échange de la protection sociale"},
    {"id": "ph5", "subject_id": "philosophie", "question": "L'existentialisme", "answer": "Sartre — L'existence précède l'essence. L'homme se définit par ses choix"},
    # SES
    {"id": "se1", "subject_id": "ses", "question": "PIB", "answer": "Produit Intérieur Brut — Mesure de la richesse créée par un pays en une année"},
    {"id": "se2", "subject_id": "ses", "question": "Inflation", "answer": "Augmentation générale et durable du niveau des prix des biens et services"},
    {"id": "se3", "subject_id": "ses", "question": "Loi de l'offre et de la demande", "answer": "Demande ↑ (offre constante) → prix ↑. Offre ↑ (demande constante) → prix ↓"},
    {"id": "se4", "subject_id": "ses", "question": "Mobilité sociale", "answer": "Changement de position sociale par rapport aux parents (intergénérationnelle) ou au cours de la vie"},
    {"id": "se5", "subject_id": "ses", "question": "Mondialisation économique", "answer": "Intégration croissante des économies nationales par les échanges commerciaux et flux financiers"},
    # Espagnol
    {"id": "es1", "subject_id": "espagnol", "question": "Ser vs Estar", "answer": "Ser = permanent (Soy español). Estar = temporaire (Estoy cansado)"},
    {"id": "es2", "subject_id": "espagnol", "question": "Pretérito indefinido", "answer": "Passé simple. Hablar → hablé, hablaste, habló, hablamos, hablasteis, hablaron"},
    {"id": "es3", "subject_id": "espagnol", "question": "Gustar", "answer": "Verbe 'plaire'. Me gusta el libro / Me gustan los libros"},
    {"id": "es4", "subject_id": "espagnol", "question": "Subjuntivo", "answer": "Mode du doute/souhait. Quiero que vengas (je veux que tu viennes)"},
    {"id": "es5", "subject_id": "espagnol", "question": "Por vs Para", "answer": "Por = cause, durée. Para = but, destination. Estudio por placer / Estudio para aprobar"},
]

async def seed_data():
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@flashcards.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "email": admin_email, "password_hash": hash_password(admin_password),
            "name": "Admin", "role": "admin", "xp": 0, "level": 1,
            "streak_count": 0, "last_study_date": None, "badges": [],
            "created_at": datetime.now(timezone.utc),
        })
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})

    # Seed subjects
    for subj in SUBJECTS_SEED:
        await db.subjects.update_one({"id": subj["id"]}, {"$set": subj}, upsert=True)

    # Seed flashcards
    for card in FLASHCARDS_SEED:
        card_doc = {**card, "created_by": None, "created_at": datetime.now(timezone.utc)}
        await db.flashcards.update_one({"id": card["id"]}, {"$set": card_doc}, upsert=True)

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.flashcards.create_index("subject_id")
    await db.user_card_progress.create_index([("user_id", 1), ("card_id", 1)], unique=True)
    await db.study_sessions.create_index("user_id")

    logger.info("Seed data loaded successfully")

@app.on_event("startup")
async def startup():
    await seed_data()

@app.on_event("shutdown")
async def shutdown():
    client.close()

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
