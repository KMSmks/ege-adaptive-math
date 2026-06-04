import random
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import generator
import models
import schemas
import seed
from database import SessionLocal, init_db

app = FastAPI(title="EGE Adaptive Math API")

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

    db = SessionLocal()
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        print("Создаём пользователя по умолчанию (id=1)...")
        db.add(models.User(username="test_student", target_score=80))
        db.commit()
    db.close()

    # Идемпотентно загружаем часть 2 (каталог) из JSON при КАЖДОМ старте.
    # seed.seed_data() сверяется по тексту и не плодит дубликаты.
    try:
        seed.seed_data()
    except Exception as e:
        print(f"Не удалось загрузить часть 2 при старте: {e}")

    # Часть 1 — параметрический генератор. Запускаем автоматически, если задач
    # части 1 мало (первый деплой / пустая база), чтобы тренажёр работал сразу,
    # без ручного вызова /run-generator/. Без бесконечного роста при рестартах.
    try:
        db = SessionLocal()
        p1_count = (
            db.query(models.Question)
            .join(models.MicroSkill)
            .join(models.Topic)
            .filter(models.Topic.is_part_two == False)  # noqa: E712
            .count()
        )
        db.close()
        if p1_count < 120:
            generator.generate_tasks(per_template=20)
    except Exception as e:
        print(f"Не удалось сгенерировать часть 1 при старте: {e}")


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

    # 1. Нормализация ввода
    user_ans = data.answer.strip().replace(",", ".").replace(" ", "")

    # Свойство части 2 берём через связь Question -> MicroSkill -> Topic
    is_part_two = question.micro_skill.topic.is_part_two

    # Часть 2 — самопроверка: ученик присылает "true"/"false"
    if is_part_two:
        is_correct = (user_ans.lower() == "true")
    else:
        correct_ans = question.correct_answer.strip().replace(",", ".").replace(" ", "") if question.correct_answer else ""
        is_correct = (user_ans == correct_ans)

    # 2. Детектор угадывания/списывания (только для части 1)
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
        mastery = models.UserSkillMastery(
            user_id=data.user_id,
            micro_skill_id=question.micro_skill_id,
            mastery_percentage=0.0,
        )
        db.add(mastery)

    # Прогресс растёт только если ответил верно И не списал
    if is_correct and not is_cheating:
        mastery.mastery_percentage = min(100.0, mastery.mastery_percentage + 15.0)
    elif not is_correct:
        mastery.mastery_percentage = max(0.0, mastery.mastery_percentage - 10.0)

    # 4. Логируем ответ для аналитики
    db.add(models.AnswerLog(
        user_id=data.user_id,
        question_id=data.question_id,
        is_correct=is_correct,
        time_spent_seconds=time_spent,
    ))

    db.commit()

    return {
        "is_correct": is_correct,
        "is_cheating": is_cheating,
        "is_part_two": is_part_two,
        "new_mastery_level": mastery.mastery_percentage,
        # Эталон отдаём ТОЛЬКО в ответе на отправку (ученик уже сдал ответ),
        # поэтому подсмотреть заранее нельзя.
        "correct_answer": question.correct_answer,
        "interval_days": 1,
    }


@app.get("/run-generator/")
def trigger_generator():
    try:
        generator.generate_tasks()
        return {"status": "success", "message": "База успешно пополнена уникальными задачами!"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/seed-from-json/")
def trigger_json_seed():
    try:
        seed.seed_data()
        return {"status": "success", "message": "Задачи из JSON успешно загружены в базу!"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/next_question/{user_id}")
def get_next_adaptive_question(user_id: int, topic_numbers: str = None,
                               exclude: int = None, db: Session = Depends(get_db)):
    # 1. Проверяем пользователя
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Берём навыки, у которых ЕСТЬ вопросы (inner join)
    query = db.query(models.MicroSkill).join(models.Question)

    # Фильтр по выбранным номерам заданий ЕГЭ
    if topic_numbers:
        try:
            task_list = [int(x) for x in topic_numbers.split(",") if x.strip()]
            query = query.join(models.Topic).filter(models.Topic.ege_task_number.in_(task_list))
        except ValueError:
            pass

    all_skills = query.distinct().all()
    if not all_skills:
        raise HTTPException(status_code=404, detail="No skills with questions available")

    # 3. Прогресс пользователя
    user_mastery = db.query(models.UserSkillMastery).filter(
        models.UserSkillMastery.user_id == user_id
    ).all()
    mastery_dict = {m.micro_skill_id: m.mastery_percentage for m in user_mastery}

    # 4. ВЗВЕШЕННЫЙ выбор навыка: чем ниже владение, тем выше шанс, но темы
    #    ротируются (а не залипают на строгом минимуме). Вес = (100 - владение + 5)^2.
    weights = []
    for skill in all_skills:
        gap = 100.0 - mastery_dict.get(skill.id, 0.0) + 5.0
        weights.append(gap * gap)

    # 5. Выбираем навык и вопрос, ИЗБЕГАЯ только что показанного вопроса.
    #    Ретраим выбор навыка: даже если у навыка один вопрос, перейдём к другой теме.
    #    Прежний вопрос вернём, только если он действительно единственный доступный.
    target_skill = None
    question = None
    for _ in range(12):
        target_skill = random.choices(all_skills, weights=weights, k=1)[0]
        questions = db.query(models.Question).filter(
            models.Question.micro_skill_id == target_skill.id
        ).all()
        pool = [q for q in questions if q.id != exclude] or questions
        question = random.choice(pool)
        if question.id != exclude:
            break

    is_part_two = target_skill.topic.is_part_two

    return {
        "question_id": question.id,
        "text": question.text,
        "image_url": question.image_url,
        "target_skill_id": target_skill.id,
        "skill_name": target_skill.name,
        "ege_task_number": target_skill.topic.ege_task_number,
        "is_part_two": is_part_two,
        "current_mastery_level": mastery_dict.get(target_skill.id, 0.0),
        # Эталон отдаём только для части 2 (режим самопроверки).
        # Для части 1 ответ не раскрываем, чтобы нельзя было подсмотреть.
        "correct_answer": question.correct_answer if is_part_two else None,
    }


@app.get("/review_today/{user_id}")
def get_review_today(user_id: int, db: Session = Depends(get_db)):
    today = datetime.utcnow()

    reviews = db.query(models.SpacedRepetition).filter(
        models.SpacedRepetition.user_id == user_id,
        models.SpacedRepetition.next_review <= today
    ).all()

    if not reviews:
        return {"message": "На сегодня нет заданий для повторения. Вы всё решили!"}

    skill_ids = [r.micro_skill_id for r in reviews]
    questions = db.query(models.Question).filter(
        models.Question.micro_skill_id.in_(skill_ids)
    ).all()

    return {
        "questions_to_review": len(questions),
        "data": [{"question_id": q.id, "text": q.text} for q in questions],
    }


@app.get("/heatmap/{user_id}")
def get_heatmap(user_id: int, db: Session = Depends(get_db)):
    """Тепловая карта, агрегированная по номерам заданий ЕГЭ (а не по микронавыкам),
    чтобы радар оставался читаемым (до 19 осей вместо десятков)."""
    mastery = db.query(models.UserSkillMastery).filter(
        models.UserSkillMastery.user_id == user_id
    ).all()
    mastery_dict = {m.micro_skill_id: m.mastery_percentage for m in mastery}

    skills = db.query(models.MicroSkill).all()

    topic_values = defaultdict(list)
    topic_names = {}
    for skill in skills:
        topic = skill.topic
        if topic is None:
            continue
        topic_values[topic.ege_task_number].append(mastery_dict.get(skill.id, 0.0))
        topic_names[topic.ege_task_number] = topic.name

    labels = []
    data_points = []
    for task_number in sorted(topic_values):
        values = topic_values[task_number]
        labels.append(f"№{task_number}. {topic_names[task_number]}")
        data_points.append(round(sum(values) / len(values), 1))

    return {"labels": labels, "data": data_points}
