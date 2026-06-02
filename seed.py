from database import SessionLocal
import models

def seed_data():
    db = SessionLocal()
    
    db.query(models.Question).delete()
    db.query(models.MicroSkill).delete()
    db.query(models.Topic).delete()
    
    # Темы
    t1 = models.Topic(ege_task_number=1, name="Планиметрия", is_part_two=False)
    t2 = models.Topic(ege_task_number=2, name="Векторы", is_part_two=False)
    t4 = models.Topic(ege_task_number=4, name="Теория вероятностей", is_part_two=False)
    t6 = models.Topic(ege_task_number=6, name="Уравнения", is_part_two=False)
    t8 = models.Topic(ege_task_number=8, name="Производная", is_part_two=False)
    db.add_all([t1, t2, t4, t6, t8])
    db.commit()

    # Микронавыки
    s1 = models.MicroSkill(name="Радиус описанной окружности", topic_id=t1.id)
    s2 = models.MicroSkill(name="Скалярное произведение", topic_id=t2.id)
    s3 = models.MicroSkill(name="Сложная вероятность", topic_id=t4.id)
    s4 = models.MicroSkill(name="Логарифмические уравнения", topic_id=t6.id)
    s5 = models.MicroSkill(name="Точки экстремума", topic_id=t8.id)
    db.add_all([s1, s2, s3, s4, s5])
    db.commit()

    # Вопросы
    q1 = models.Question(text="В треугольнике АВС сторона АВ = 3√2, угол С = 135. Найдите радиус описанной окружности.", correct_answer="3", micro_skill_id=s1.id)
    q2 = models.Question(text="Даны векторы a(3;4) и b(-4;-3). Найдите косинус угла между ними.", correct_answer="-0.96", micro_skill_id=s2.id)
    q3 = models.Question(text="Механические часы сломались. Найдите вероятность того, что часовая стрелка остановилась между 7 и 1.", correct_answer="0.5", micro_skill_id=s3.id)
    q4 = models.Question(text="Найдите корень уравнения 3^{log_27(2x-9)} = 3.", correct_answer="18", micro_skill_id=s4.id)
    db.add_all([q1, q2, q3, q4])
    db.commit()
    
    db.close()

if __name__ == "__main__":
    seed_data()