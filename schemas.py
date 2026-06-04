from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    target_score: int = 80

class UserAuth(BaseModel):
    username: str
    password: str # Добавили поле для валидации входящего пароля

class AnswerSubmit(BaseModel):
    user_id: int
    question_id: int
    answer: str
    time_spent_seconds: Optional[int] = 0