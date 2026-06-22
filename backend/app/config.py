import os

# ─── JWT ───
JWT_ALGORITHM = "HS256"


def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


# ─── GRADE LEVELS ───
GRADE_LEVELS = ["6eme", "5eme", "4eme", "3eme", "2nde", "1ere", "terminale"]
GRADE_ORDER = {g: i for i, g in enumerate(GRADE_LEVELS)}  # 6eme=0 ... terminale=6

COLLEGE = ["6eme", "5eme", "4eme", "3eme"]
LYCEE = ["2nde", "1ere", "terminale"]


def grades_from_min(min_grade: str) -> list:
    """Return all grades from min_grade up to terminale (inclusive)."""
    idx = GRADE_ORDER.get(min_grade, 0)
    return GRADE_LEVELS[idx:]


def grades_up_to(user_grade: str) -> list:
    """Return all grades from 6eme up to user_grade (inclusive)."""
    idx = GRADE_ORDER.get(user_grade, 6)
    return GRADE_LEVELS[: idx + 1]


# ─── GAMIFICATION ───
DAILY_REWARD_XP = [25, 50, 75, 100, 150, 200, 300]  # Day 1-7 cycle

WEEKLY_CHALLENGES = [
    {"id": "sessions_5", "type": "sessions", "title": "Marathonien", "description": "Complète 5 sessions cette semaine", "target": 5, "xp_reward": 200, "icon": "albums-outline"},
    {"id": "perfect_2", "type": "perfect", "title": "Sans faute", "description": "Obtiens 100% sur 2 sessions", "target": 2, "xp_reward": 300, "icon": "star-outline"},
    {"id": "subjects_3", "type": "subjects", "title": "Touche-à-tout", "description": "Étudie 3 matières différentes", "target": 3, "xp_reward": 150, "icon": "grid-outline"},
    {"id": "master_5", "type": "master", "title": "Maître absolu", "description": "Déplace 5 cartes en boîte 3", "target": 5, "xp_reward": 250, "icon": "trophy-outline"},
]

BADGE_DEFS = [
    {"id": "first_step", "name": "Premier Pas", "description": "Première session complétée", "icon": "rocket-outline"},
    {"id": "perfectionist", "name": "Perfectionniste", "description": "100% à une session", "icon": "star-outline"},
    {"id": "on_fire_3", "name": "En Feu", "description": "3 jours consécutifs", "icon": "flame-outline"},
    {"id": "marathon_7", "name": "Marathonien", "description": "7 jours consécutifs", "icon": "medal-outline"},
    {"id": "expert", "name": "Expert", "description": "Niveau 5 atteint", "icon": "trophy-outline"},
    {"id": "master", "name": "Maître", "description": "10 cartes en boîte 3", "icon": "school-outline"},
]
