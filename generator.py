import random
from database import SessionLocal
import models

def generate_tasks():
    db = SessionLocal()
    
    # Достаем навыки из базы (созданные ранее через seed.py)
    skill_log = db.query(models.MicroSkill).filter_by(name="Логарифмические уравнения").first()
    skill_geom = db.query(models.MicroSkill).filter_by(name="Радиус описанной окружности").first()
    
    if not skill_log or not skill_geom:
        print("Сначала запустите seed.py, чтобы создать структуру тем!")
        return

    questions = []

    # 1. Генерируем 50 задач на логарифмы: log_A(B*x + C) = D
    # Математика: A^D = B*x + C  =>  x = (A^D - C) / B
    for _ in range(50):
        A = random.choice([2, 3, 4, 5])
        D = random.randint(1, 3)
        B = random.choice([1, 2, 4, 5]) # Коэффициенты, дающие красивые дроби
        
        # Подбираем C так, чтобы x_ans был целым (от -15 до 15)
        x_ans = random.randint(-15, 15)
        C = (A**D) - B * x_ans
        
        sign = "+" if C >= 0 else "-"
        text = f"Найдите корень уравнения log_{A}({B}x {sign} {abs(C)}) = {D}."
        
        questions.append(models.Question(
            text=text,
            correct_answer=str(x_ans),
            micro_skill_id=skill_log.id,
            difficulty=random.randint(1, 3)
        ))

    # 2. Генерируем 50 задач на геометрию (Радиус по теореме синусов)
    # Математика: R = AB / (2 * sin(C))
    angles = {
        30: ("1/2", 0.5), 
        150: ("1/2", 0.5),
        45: ("√2/2", 0.7071), 
        135: ("√2/2", 0.7071),
        60: ("√3/2", 0.866), 
        120: ("√3/2", 0.866)
    }
    
    for _ in range(50):
        angle, (sin_str, sin_val) = random.choice(list(angles.items()))
        R_ans = random.randint(2, 20)
        
        # Формируем красивую длину стороны АВ для условия
        if "√" in sin_str:
            root_part = sin_str.split('/')[0] # √2 или √3
            AB_str = f"{R_ans}{root_part}" # Например, 5√2
        else:
            AB_str = str(R_ans)
            
        text = f"В треугольнике АВС сторона АВ = {AB_str}, угол С = {angle}°. Найдите радиус описанной окружности."
        
        questions.append(models.Question(
            text=text,
            correct_answer=str(R_ans),
            micro_skill_id=skill_geom.id,
            difficulty=random.randint(1, 3)
        ))

    # Сохраняем всё в базу
    db.add_all(questions)
    db.commit()
    db.close()
    
    print(f"Успешно сгенерировано и добавлено {len(questions)} уникальных задач!")

if __name__ == "__main__":
    generate_tasks()