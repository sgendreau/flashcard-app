import os
import logging
from datetime import datetime, timezone

from app.config import GRADE_LEVELS, grades_from_min
from app.db import db
from app.security import hash_password, verify_password
from app.helpers import generate_referral_code

logger = logging.getLogger(__name__)


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

# grade_levels = grades from min_grade to terminale (inclusive)
FLASHCARDS_SEED = [
    # Maths
    {"id": "m1", "subject_id": "maths", "question": "Théorème de Pythagore", "answer": "Dans un triangle rectangle, a² + b² = c²", "grade_levels": grades_from_min("6eme")},
    {"id": "m2", "subject_id": "maths", "question": "Identité remarquable (a+b)²", "answer": "(a+b)² = a² + 2ab + b²", "grade_levels": grades_from_min("3eme")},
    {"id": "m3", "subject_id": "maths", "question": "Aire d'un cercle", "answer": "A = πr² où r est le rayon", "grade_levels": grades_from_min("6eme")},
    {"id": "m4", "subject_id": "maths", "question": "PGCD", "answer": "Plus Grand Commun Diviseur de deux entiers", "grade_levels": grades_from_min("5eme")},
    {"id": "m5", "subject_id": "maths", "question": "Fonction affine", "answer": "f(x) = ax + b, droite de pente a", "grade_levels": grades_from_min("3eme")},
    # Français
    {"id": "f1", "subject_id": "francais", "question": "Métaphore", "answer": "Comparaison sans outil de comparaison", "grade_levels": grades_from_min("6eme")},
    {"id": "f2", "subject_id": "francais", "question": "Oxymore", "answer": "Association de deux termes contraires. Ex: 'obscure clarté'", "grade_levels": grades_from_min("3eme")},
    {"id": "f3", "subject_id": "francais", "question": "Alexandrin", "answer": "Vers de 12 syllabes", "grade_levels": grades_from_min("6eme")},
    {"id": "f4", "subject_id": "francais", "question": "Champ lexical", "answer": "Ensemble de mots d'un même thème", "grade_levels": grades_from_min("6eme")},
    {"id": "f5", "subject_id": "francais", "question": "Hyperbole", "answer": "Exagération pour frapper l'esprit", "grade_levels": grades_from_min("6eme")},
    # Histoire-Géo
    {"id": "h1", "subject_id": "histoire_geo", "question": "Révolution française", "answer": "1789 — Fin de la monarchie absolue", "grade_levels": grades_from_min("6eme")},
    {"id": "h2", "subject_id": "histoire_geo", "question": "Première Guerre mondiale", "answer": "1914-1918 — Conflit mondial, 10M de morts", "grade_levels": grades_from_min("3eme")},
    {"id": "h3", "subject_id": "histoire_geo", "question": "Débarquement en Normandie", "answer": "6 juin 1944 (Jour J)", "grade_levels": grades_from_min("3eme")},
    {"id": "h4", "subject_id": "histoire_geo", "question": "Les Trente Glorieuses", "answer": "Croissance économique 1945-1975", "grade_levels": grades_from_min("2nde")},
    {"id": "h5", "subject_id": "histoire_geo", "question": "La mondialisation", "answer": "Intégration mondiale des marchés et sociétés", "grade_levels": grades_from_min("2nde")},
    # SVT
    {"id": "s1", "subject_id": "svt", "question": "Photosynthèse", "answer": "CO₂ + eau → glucose + O₂ (lumière)", "grade_levels": grades_from_min("6eme")},
    {"id": "s2", "subject_id": "svt", "question": "ADN", "answer": "Molécule de l'information génétique, double hélice", "grade_levels": grades_from_min("3eme")},
    {"id": "s3", "subject_id": "svt", "question": "Mitose", "answer": "Division cellulaire → 2 cellules identiques", "grade_levels": grades_from_min("3eme")},
    {"id": "s4", "subject_id": "svt", "question": "Tectonique des plaques", "answer": "Mouvement des plaques lithosphériques", "grade_levels": grades_from_min("6eme")},
    {"id": "s5", "subject_id": "svt", "question": "Écosystème", "answer": "Communauté vivante + environnement physique", "grade_levels": grades_from_min("6eme")},
    # Physique-Chimie
    {"id": "p1", "subject_id": "physique_chimie", "question": "Loi d'Ohm", "answer": "U = R × I", "grade_levels": grades_from_min("4eme")},
    {"id": "p2", "subject_id": "physique_chimie", "question": "Énergie cinétique", "answer": "Ec = ½mv²", "grade_levels": grades_from_min("2nde")},
    {"id": "p3", "subject_id": "physique_chimie", "question": "Atome", "answer": "Noyau (protons+neutrons) + électrons", "grade_levels": grades_from_min("6eme")},
    {"id": "p4", "subject_id": "physique_chimie", "question": "Vitesse de la lumière", "answer": "c ≈ 3×10⁸ m/s", "grade_levels": grades_from_min("4eme")},
    {"id": "p5", "subject_id": "physique_chimie", "question": "pH", "answer": "<7 acide, =7 neutre, >7 basique", "grade_levels": grades_from_min("3eme")},
    # Anglais
    {"id": "a1", "subject_id": "anglais", "question": "Present Perfect", "answer": "Have/Has + past participle", "grade_levels": grades_from_min("6eme")},
    {"id": "a2", "subject_id": "anglais", "question": "Conditional (2nd)", "answer": "If + past simple, would + verb", "grade_levels": grades_from_min("3eme")},
    {"id": "a3", "subject_id": "anglais", "question": "To look forward to", "answer": "Attendre avec impatience", "grade_levels": grades_from_min("6eme")},
    {"id": "a4", "subject_id": "anglais", "question": "Passive voice", "answer": "Subject + be + past participle", "grade_levels": grades_from_min("4eme")},
    {"id": "a5", "subject_id": "anglais", "question": "Since vs For", "answer": "Since = point. For = durée", "grade_levels": grades_from_min("6eme")},
    # Philosophie (Terminale min)
    {"id": "ph1", "subject_id": "philosophie", "question": "Cogito ergo sum", "answer": "Je pense donc je suis — Descartes", "grade_levels": grades_from_min("terminale")},
    {"id": "ph2", "subject_id": "philosophie", "question": "L'allégorie de la caverne", "answer": "Platon — Ombres vs réalité", "grade_levels": grades_from_min("terminale")},
    {"id": "ph3", "subject_id": "philosophie", "question": "L'impératif catégorique", "answer": "Kant — Maxime érigeable en loi universelle", "grade_levels": grades_from_min("terminale")},
    {"id": "ph4", "subject_id": "philosophie", "question": "Le contrat social", "answer": "Rousseau — Liberté contre protection", "grade_levels": grades_from_min("terminale")},
    {"id": "ph5", "subject_id": "philosophie", "question": "L'existentialisme", "answer": "Sartre — L'existence précède l'essence", "grade_levels": grades_from_min("terminale")},
    # SES (2nde min)
    {"id": "se1", "subject_id": "ses", "question": "PIB", "answer": "Produit Intérieur Brut — Richesse annuelle", "grade_levels": grades_from_min("2nde")},
    {"id": "se2", "subject_id": "ses", "question": "Inflation", "answer": "Hausse générale et durable des prix", "grade_levels": grades_from_min("2nde")},
    {"id": "se3", "subject_id": "ses", "question": "Loi offre/demande", "answer": "Demande↑→prix↑, Offre↑→prix↓", "grade_levels": grades_from_min("2nde")},
    {"id": "se4", "subject_id": "ses", "question": "Mobilité sociale", "answer": "Changement de position entre générations", "grade_levels": grades_from_min("1ere")},
    {"id": "se5", "subject_id": "ses", "question": "Mondialisation économique", "answer": "Intégration des économies nationales", "grade_levels": grades_from_min("terminale")},
    # Espagnol
    {"id": "es1", "subject_id": "espagnol", "question": "Ser vs Estar", "answer": "Ser=permanent, Estar=temporaire", "grade_levels": grades_from_min("6eme")},
    {"id": "es2", "subject_id": "espagnol", "question": "Pretérito indefinido", "answer": "Passé simple: hablé, hablaste, habló...", "grade_levels": grades_from_min("4eme")},
    {"id": "es3", "subject_id": "espagnol", "question": "Gustar", "answer": "Me gusta/gustan = ça me plaît", "grade_levels": grades_from_min("6eme")},
    {"id": "es4", "subject_id": "espagnol", "question": "Subjuntivo", "answer": "Mode du doute/souhait", "grade_levels": grades_from_min("2nde")},
    {"id": "es5", "subject_id": "espagnol", "question": "Por vs Para", "answer": "Por=cause/durée, Para=but/destination", "grade_levels": grades_from_min("3eme")},
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
            "referral_code": generate_referral_code(), "referred_by": None, "referral_count": 0,
            "created_at": datetime.now(timezone.utc),
        })
    else:
        # Update existing admin: password if changed, add referral_code if missing
        updates = {}
        if not verify_password(admin_password, existing["password_hash"]):
            updates["password_hash"] = hash_password(admin_password)
        if not existing.get("referral_code"):
            updates["referral_code"] = generate_referral_code()
        if "referral_count" not in existing:
            updates["referral_count"] = 0
        if updates:
            await db.users.update_one({"email": admin_email}, {"$set": updates})

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
    await db.users.create_index("referral_code", unique=True, sparse=True)
    logger.info("Seed data loaded successfully")
