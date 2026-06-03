"""
Генератор заданий из параметрических шаблонов (templates.py).

Берёт каждый шаблон, создаёт при необходимости Тему и Микронавык
(по позиционной карте templates.TASK_TOPICS) и добавляет per_template
уникальных задач. Дедуп — по тексту, поэтому повторный запуск безопасен.
"""
import random

import models
import templates
from database import SessionLocal


def _get_or_create_topic(db, task_number):
    name, is_part_two = templates.TASK_TOPICS[task_number]
    topic = db.query(models.Topic).filter_by(ege_task_number=task_number).first()
    if not topic:
        topic = models.Topic(ege_task_number=task_number, name=name, is_part_two=is_part_two)
        db.add(topic)
        db.commit()
        db.refresh(topic)
    return topic


def _get_or_create_skill(db, topic_id, name):
    skill = db.query(models.MicroSkill).filter_by(name=name, topic_id=topic_id).first()
    if not skill:
        skill = models.MicroSkill(name=name, topic_id=topic_id)
        db.add(skill)
        db.commit()
        db.refresh(skill)
    return skill


def generate_tasks(per_template=20):
    db = SessionLocal()
    added = 0
    try:
        for tpl in templates.TEMPLATES:
            topic = _get_or_create_topic(db, tpl["task"])
            skill = _get_or_create_skill(db, topic.id, tpl["skill"])

            seen = set()
            made = 0
            attempts = 0
            while made < per_template and attempts < per_template * 30:
                attempts += 1
                text, answer = tpl["fn"]()
                if text in seen:
                    continue
                seen.add(text)
                if db.query(models.Question).filter_by(text=text).first():
                    continue
                db.add(models.Question(
                    text=text,
                    correct_answer=answer,
                    micro_skill_id=skill.id,
                    difficulty=tpl.get("difficulty", 1),
                ))
                made += 1
                added += 1
            db.commit()
        print(f"Сгенерировано и добавлено уникальных задач: {added}")
        return added
    finally:
        db.close()


if __name__ == "__main__":
    generate_tasks()
