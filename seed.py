from database import SessionLocal
import models

def seed_data():
    db = SessionLocal()
    
    # Очистка
    db.query(models.Question).delete()
    db.query(models.MicroSkill).delete()
    db.query(models.Topic).delete()
    
    # Темы
    t1 = models.Topic(ege_task_number=1, name="Планиметрия")
    t2 = models.Topic(ege_task_number=6, name="Уравнения")
    db.add_all([t1, t2])
    db.commit()

    # Навыки
    s1 = models.MicroSkill(name="Радиус описанной окружности", topic_id=t1.id)
    s2 = models.MicroSkill(name="Логарифмические уравнения", topic_id=t2.id)
    db.add_all([s1, s2])
    db.commit()

    # Вопросы (без указания сложности, чтобы использовать значения по умолчанию)
    q1 = models.Question(
        text="В треугольнике АВС сторона АВ = 3√2, угол С = 135. Найдите радиус описанной окружности.",
        correct_answer="3",
        micro_skill_id=s1.id
    )
    q2 = models.Question(
        text="Найдите корень уравнения 3^{log_27(2x-9)} = 3.",
        correct_answer="18",
        micro_skill_id=s2.id
    )
    db.add_all([q1, q2])
    db.commit()
    
    db.close()
    print("База успешно заполнена!")

if __name__ == "__main__":
    seed_data()