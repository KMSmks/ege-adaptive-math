from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
import models, schemas
from fastapi.responses import HTMLResponse

app = FastAPI(title="EGE Adaptive Math API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    
    # Автоматическое заполнение базы, если она пустая
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.id == 1).first()
    
    if not user:
        print("База пустая. Создаем пользователя и загружаем вопросы...")
        # Создаем пользователя с ID 1, которого ищет фронтенд
        new_user = models.User(username="test_student", target_score=80)
        db.add(new_user)
        db.commit()
        
        # Вызываем скрипт заполнения вопросов
        import seed
        seed.seed_data()
        
    db.close()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/users/")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(username=user.username, target_score=user.target_score)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "username": db_user.username}

@app.post("/submit_answer/")
def submit_answer(data: schemas.AnswerSubmit, db: Session = Depends(get_db)):
    question = db.query(models.Question).filter(models.Question.id == data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # 1. Оптимизация ввода
    user_ans = data.answer.strip().replace(",", ".").replace(" ", "")
    
    # Дотягиваемся до свойства темы через графы связей SQLAlchemy
    is_part_two = question.micro_skill.topic.is_part_two
    
    # Обработка второй части
    if is_part_two:
        is_correct = (user_ans.lower() == "true")
    else:
        correct_ans = question.correct_answer.strip().replace(",", ".").replace(" ", "") if question.correct_answer else ""
        is_correct = (user_ans == correct_ans)

    # 2. Детектор угадывания/списывания
    is_cheating = False
    time_spent = data.time_spent_seconds if data.time_spent_seconds else 0
    
    if not is_part_two and time_spent > 0 and time_spent < 5:
        is_cheating = True 

    # 3. Обновляем тепловую карту
    mastery = db.query(models.UserSkillMastery).filter(
        models.UserSkillMastery.user_id == data.user_id,
        models.UserSkillMastery.micro_skill_id == question.micro_skill_id
    ).first()
    
    if not mastery:
        mastery = models.UserSkillMastery(user_id=data.user_id, micro_skill_id=question.micro_skill_id, mastery_percentage=0.0)
        db.add(mastery)
    
    # Прогресс растет только если ответил верно И не списал
    if is_correct and not is_cheating:
        mastery.mastery_percentage = min(100.0, mastery.mastery_percentage + 15.0)
    elif not is_correct:
        mastery.mastery_percentage = max(0.0, mastery.mastery_percentage - 10.0)

    # 4. Логируем ответ для аналитики репетитора
    log = models.AnswerLog(
        user_id=data.user_id, 
        question_id=data.question_id, 
        is_correct=is_correct, 
        time_spent_seconds=time_spent
    )
    db.add(log)
    
    db.commit()
    
    return {
        "is_correct": is_correct,
        "is_cheating": is_cheating,
        "new_mastery_level": mastery.mastery_percentage,
        "interval_days": 1  # Добавили недостающее поле для фронтенда
    }

@app.get("/next_question/{user_id}")
def get_next_adaptive_question(user_id: int, db: Session = Depends(get_db)):
    # 1. Проверяем, существует ли пользователь
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Ищем все микронавыки
    all_skills = db.query(models.MicroSkill).all()
    if not all_skills:
        raise HTTPException(status_code=404, detail="No skills in DB")

    # 3. Получаем прогресс пользователя
    user_mastery = db.query(models.UserSkillMastery).filter(
        models.UserSkillMastery.user_id == user_id
    ).all()
    
    mastery_dict = {m.micro_skill_id: m.mastery_percentage for m in user_mastery}

    # 4. Логика адаптивности: ищем навык с минимальным % владения (или 0.0, если еще не решал)
    target_skill_id = all_skills[0].id
    min_mastery = 101.0

    for skill in all_skills:
        current_mastery = mastery_dict.get(skill.id, 0.0)
        if current_mastery < min_mastery:
            min_mastery = current_mastery
            target_skill_id = skill.id

    # 5. Выбираем вопрос по этому навыку
    question = db.query(models.Question).filter(
        models.Question.micro_skill_id == target_skill_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="No questions available for target skill")

    return {
        "question_id": question.id,
        "text": question.text,
        "target_skill_id": target_skill_id,
        "current_mastery_level": min_mastery
    }


@app.get("/review_today/{user_id}")
def get_review_today(user_id: int, db: Session = Depends(get_db)):
    today = datetime.utcnow()
    
    # Ищем навыки, которые пора повторить
    reviews = db.query(models.SpacedRepetition).filter(
        models.SpacedRepetition.user_id == user_id,
        models.SpacedRepetition.next_review <= today
    ).all()
    
    if not reviews:
        return {"message": "На сегодня нет заданий для повторения. Вы всё решили!"}
        
    skill_ids = [r.micro_skill_id for r in reviews]
    
    # Собираем вопросы по этим навыкам
    questions = db.query(models.Question).filter(
        models.Question.micro_skill_id.in_(skill_ids)
    ).all()
    
    return {
        "questions_to_review": len(questions),
        "data": [{"question_id": q.id, "text": q.text} for q in questions]
    }


@app.get("/heatmap/{user_id}")
def get_heatmap(user_id: int, db: Session = Depends(get_db)):
    skills = db.query(models.MicroSkill).all()
    mastery = db.query(models.UserSkillMastery).filter(models.UserSkillMastery.user_id == user_id).all()
    
    mastery_dict = {m.micro_skill_id: m.mastery_percentage for m in mastery}
    
    labels = []
    data_points = []
    
    for skill in skills:
        labels.append(skill.name)
        data_points.append(mastery_dict.get(skill.id, 0.0))
        
    return {
        "labels": labels,
        "data": data_points
    }