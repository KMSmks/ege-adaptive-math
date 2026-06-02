from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    target_score: int = 80

class AnswerSubmit(BaseModel):
    user_id: int
    question_id: int
    answer: str