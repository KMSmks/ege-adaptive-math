
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
                result = tpl["fn"]()
                
                
                if isinstance(result, dict):
                    text = result["text"]
                    answer = result["answer"]
                    image_url = result.get("image_url")
                    solution = result.get("solution")
                else:
                    text, answer = result[0], result[1]
                    image_url = result[2] if len(result) >= 3 else None
                    solution = result[3] if len(result) >= 4 else None
                if text in seen:
                    continue
                seen.add(text)
                if db.query(models.Question).filter_by(text=text).first():
                    continue
                db.add(models.Question(
                    text=text,
                    correct_answer=answer,
                    image_url=image_url,
                    solution=solution,
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
