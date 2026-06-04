import random
import hashlib
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
import templates
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

    try:
        seed.seed_data()
    except Exception as e:
        print(f"Не удалось загрузить часть 2 при старте: {e}")

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


@app.post("/auth/")
def login_or_register(data: schemas.UserAuth, db: Session = Depends(get_db)):
    """Авторизация по логину и паролю. Если пользователя нет — регистрируем с указанным паролем.

    Если есть — проверяем соответствие хэша.
    """
    # Вычисляем SHA-256 хэш от пароля ученика
    pwd_hash = hashlib.sha256(data.password.encode("utf-8")).hexdigest()
    
    db_user = db.query(models.User).filter(models.User.username == data.username).first()
    
    if not db_user:
        # Автоматическая регистрация нового пользователя, если ник свободен
        db_user = models.User(username=data.username, password_hash=pwd_hash, target_score=80)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"id": db_user.id, "username": db_user.username, "status": "registered"}
    
    # Обратная совместимость для старых тестовых пользователей без пароля (если password_hash — NULL)
    if db_user.password_hash is None:
        db_user.password_hash = pwd_hash
        db.commit()
        db.refresh(db_user)
    elif db_user.password_hash != pwd_hash:
        # Если пароль не подошёл — отдаем HTTP 401 Unauthorized
        raise HTTPException(status_code=401, detail="Неверный пароль для данного пользователя")
        
    return {"id": db_user.id, "username": db_user.username, "status": "logged_in"}


def _sm2_update(db, user_id, micro_skill_id, quality):
    """Обновляет карточку интервального повторения по алгоритму SM-2."""
    card = db.query(models.SpacedRepetition).filter(
        models.SpacedRepetition.user_id == user_id,
        models.SpacedRepetition.micro_skill_id == micro_skill_id,
    ).first()
    if not card:
        card = models.SpacedRepetition(
            user_id=user_id, micro_skill_id=micro_skill_id,
            interval=1, ease_factor=2.5, repetitions=0,
        )
        db.add(card)

    if quality < 3:
        card.repetitions = 0
        card.interval = 1
    else:
        if card.repetitions == 0:
            card.interval = 1
        elif card.repetitions == 1:
            card.interval = 6
        else:
            card.interval = max(1, int(round(card.interval * card.ease_factor)))
        card.repetitions += 1

    ef = card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    card.ease_factor = max(1.3, ef)
    card.next_review = datetime.utcnow() + timedelta(days=card.interval)
    return card.interval


def _quality_from_answer(is_correct, is_cheating, time_spent):
    if not is_correct:
        return 2 if time_spent >= 5 else 1
    if is_cheating:
        return 3
    if time_spent and time_spent < 30:
        return 5
    return 4


@app.post("/submit_answer/")
def submit_answer(data: schemas.AnswerSubmit, db: Session = Depends(get_db)):
    question = db.query(models.Question).filter(models.Question.id == data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    user_ans = data.answer.strip().replace(",", ".").replace(" ", "")
    is_part_two = question.micro_skill.topic.is_part_two

    if is_part_two:
        is_correct = (user_ans.lower() == "true")
    else:
        correct_ans = question.correct_answer.strip().replace(",", ".").replace(" ", "") if question.correct_answer else ""
        is_correct = (user_ans == correct_ans)

    is_cheating = False
    time_spent = data.time_spent_seconds if data.time_spent_seconds else 0
    if not is_part_two and time_spent > 0 and time_spent < 5:
        is_cheating = True

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

    if is_correct and not is_cheating:
        mastery.mastery_percentage = min(100.0, mastery.mastery_percentage + 15.0)
    elif not is_correct:
        mastery.mastery_percentage = max(0.0, mastery.mastery_percentage - 10.0)

    db.add(models.AnswerLog(
        user_id=data.user_id,
        question_id=data.question_id,
        is_correct=is_correct,
        time_spent_seconds=time_spent,
    ))

    quality = _quality_from_answer(is_correct, is_cheating, time_spent)
    interval_days = _sm2_update(db, data.user_id, question.micro_skill_id, quality)

    db.commit()

    return {
        "is_correct": is_correct,
        "is_cheating": is_cheating,
        "is_part_two": is_part_two,
        "new_mastery_level": mastery.mastery_percentage,
        "correct_answer": question.correct_answer,
        "solution": question.solution,
        "interval_days": interval_days,
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
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    query = db.query(models.MicroSkill).join(models.Question)

    if topic_numbers:
        try:
            task_list = [int(x) for x in topic_numbers.split(",") if x.strip()]
            query = query.join(models.Topic).filter(models.Topic.ege_task_number.in_(task_list))
        except ValueError:
            pass

    all_skills = query.distinct().all()
    if not all_skills:
        raise HTTPException(status_code=404, detail="No skills with questions available")

    user_mastery = db.query(models.UserSkillMastery).filter(
        models.UserSkillMastery.user_id == user_id
    ).all()
    mastery_dict = {m.micro_skill_id: m.mastery_percentage for m in user_mastery}

    weights = []
    for skill in all_skills:
        gap = 100.0 - mastery_dict.get(skill.id, 0.0) + 5.0
        weights.append(gap * gap)

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
        "correct_answer": question.correct_answer if is_part_two else None,
        "solution": question.solution if is_part_two else None,
    }


@app.get("/review_today/{user_id}")
def get_review_today(user_id: int, db: Session = Depends(get_db)):
    today = datetime.utcnow()

    reviews = db.query(models.SpacedRepetition).filter(
        models.SpacedRepetition.user_id == user_id,
        models.SpacedRepetition.next_review <= today
    ).all()

    skill_ids = [r.micro_skill_id for r in reviews]
    if not skill_ids:
        return {"questions_to_review": 0, "skill_ids": [], "message":
                "На сегодня нет заданий для повторения. Вы всё решили!"}

    available = (
        db.query(models.MicroSkill.id)
        .join(models.Question)
        .filter(models.MicroSkill.id.in_(skill_ids))
        .distinct().all()
    )
    available_ids = [a[0] for a in available]
    return {"questions_to_review": len(available_ids), "skill_ids": available_ids}


@app.get("/next_review_question/{user_id}")
def get_next_review_question(user_id: int, exclude: int = None, db: Session = Depends(get_db)):
    today = datetime.utcnow()
    due = db.query(models.SpacedRepetition).filter(
        models.SpacedRepetition.user_id == user_id,
        models.SpacedRepetition.next_review <= today,
    ).all()
    due_skill_ids = [r.micro_skill_id for r in due]
    if not due_skill_ids:
        raise HTTPException(status_code=404, detail="Нет карточек к повторению")

    questions = db.query(models.Question).filter(
        models.Question.micro_skill_id.in_(due_skill_ids)
    ).all()
    if not questions:
        raise HTTPException(status_code=404, detail="Нет вопросов для повторения")

    pool = [q for q in questions if q.id != exclude] or questions
    question = random.choice(pool)
    skill = question.micro_skill
    is_part_two = skill.topic.is_part_two
    return {
        "question_id": question.id,
        "text": question.text,
        "image_url": question.image_url,
        "target_skill_id": skill.id,
        "skill_name": skill.name,
        "ege_task_number": skill.topic.ege_task_number,
        "is_part_two": is_part_two,
        "correct_answer": question.correct_answer if is_part_two else None,
        "solution": question.solution if is_part_two else None,
    }


@app.get("/heatmap/{user_id}")
def get_heatmap(user_id: int, db: Session = Depends(get_db)):
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


TASK_MAX = {**{i: 1 for i in range(1, 13)}, 13: 2, 14: 3, 15: 2, 16: 2, 17: 3, 18: 4, 19: 4}

PRIMARY_TO_SECONDARY = {
    0: 0, 1: 5, 2: 9, 3: 14, 4: 18, 5: 23, 6: 27, 7: 33, 8: 39, 9: 45, 10: 50,
    11: 56, 12: 62, 13: 68, 14: 70, 15: 72, 16: 74, 17: 76, 18: 78, 19: 80, 20: 82,
    21: 84, 22: 86, 23: 88, 24: 90, 25: 92, 26: 94, 27: 96, 28: 98, 29: 99, 30: 99,
    31: 100, 32: 100,
}


def _primary_to_secondary(primary: float) -> int:
    lo = int(primary)
    hi = min(lo + 1, 32)
    frac = primary - lo
    s = PRIMARY_TO_SECONDARY[lo] + (PRIMARY_TO_SECONDARY[hi] - PRIMARY_TO_SECONDARY[lo]) * frac
    return int(round(s))


@app.get("/score_forecast/{user_id}")
def score_forecast(user_id: int, db: Session = Depends(get_db)):
    mastery = db.query(models.UserSkillMastery).filter(
        models.UserSkillMastery.user_id == user_id
    ).all()
    mastery_dict = {m.micro_skill_id: m.mastery_percentage for m in mastery}

    skills = db.query(models.MicroSkill).all()
    by_task = defaultdict(list)
    for s in skills:
        if s.topic:
            by_task[s.topic.ege_task_number].append(mastery_dict.get(s.id, 0.0))

    expected_primary = 0.0
    growth = []
    for task, mx in TASK_MAX.items():
        vals = by_task.get(task, [0.0])
        avg = sum(vals) / len(vals)
        p = avg / 100.0
        expected_primary += p * mx
        topic_name = templates.TASK_TOPICS.get(task, (f"Задание {task}", False))[0]
        growth.append({
            "task": task,
            "name": topic_name,
            "mastery": round(avg, 1),
            "potential": round(mx * (1 - p), 3),
        })

    growth.sort(key=lambda g: g["potential"], reverse=True)
    expected_primary = round(expected_primary, 1)

    return {
        "expected_primary": expected_primary,
        "max_primary": sum(TASK_MAX.values()),
        "expected_secondary": _primary_to_secondary(expected_primary),
        "focus": growth[:3],
    }