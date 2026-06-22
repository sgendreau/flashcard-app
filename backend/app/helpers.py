import random
import string
from datetime import datetime, timezone, timedelta


def generate_class_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_referral_code() -> str:
    return "FC" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))


def get_week_start():
    today = datetime.now(timezone.utc).date()
    return today - timedelta(days=today.weekday())


def user_response(user_doc, user_id=None) -> dict:
    """Public-safe representation of a user document."""
    uid = user_id or str(user_doc.get("_id", ""))
    return {
        "id": uid, "email": user_doc["email"], "name": user_doc["name"],
        "xp": user_doc.get("xp", 0), "level": user_doc.get("level", 1),
        "streak_count": user_doc.get("streak_count", 0),
        "badges": user_doc.get("badges", []), "role": user_doc.get("role", "student"),
        "grade_level": user_doc.get("grade_level"),
        "notification_enabled": user_doc.get("notification_enabled", True),
        "notification_hour": user_doc.get("notification_hour", 18),
        "theme": user_doc.get("theme", "light"),
        "referral_code": user_doc.get("referral_code", ""),
    }
