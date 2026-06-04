import json
from database import SessionLocal
import models

def seed_data():
    db = SessionLocal()
    
    try:
        with open("questions_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        added_questions = 0
        
        for item in data:
            # 1. Ищем или создаем Тему
            topic = db.query(models.Topic).filter_by(ege_task_number=item["topic_number"]).first()
            if not topic:
                topic = models.Topic(ege_task_number=item["topic_number"], name=item["topic_name"], is_part_two=item.get("is_part_two", False))
                db.add(topic)
                db.commit()
                db.refresh(topic)

            # 2. Ищем или создаем Навык
            skill = db.query(models.MicroSkill).filter_by(name=item["skill_name"], topic_id=topic.id).first()
            if not skill:
                skill = models.MicroSkill(name=item["skill_name"], topic_id=topic.id)
                db.add(skill)
                db.commit()
                db.refresh(skill)

            # 3. Добавляем вопрос (проверяем, нет ли уже такого текста в базе)
            existing_q = db.query(models.Question).filter_by(text=item["text"]).first()
            if not existing_q:
                new_q = models.Question(
                    text=item["text"],
                    image_url=item.get("image_url"),
                    correct_answer=item["correct_answer"],
                    solution=item.get("solution"),
                    micro_skill_id=skill.id
                )
                db.add(new_q)
                added_questions += 1
            elif item.get("solution") and existing_q.solution != item["solution"]:
                # Обновляем решение, если оно изменилось в JSON (например, добавили картинку)
                existing_q.solution = item["solution"]
                
        db.commit()
        print(f"База обновлена! Добавлено новых задач: {added_questions}")
        
    except FileNotFoundError:
        print("Файл questions_data.json не найден!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()