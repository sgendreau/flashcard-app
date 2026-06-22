from typing import List, Optional

from pydantic import BaseModel


class RegisterInput(BaseModel):
    name: str
    email: str
    password: str
    referral_code: Optional[str] = None
    is_admin: bool = False
    is_student: bool = True


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
    source: str = "officiel"


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


class AIGenerateInput(BaseModel):
    subject_id: str
    text: str
    count: int = 5
