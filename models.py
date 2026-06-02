from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    # Целевой балл, к которому стремится ученик (поможет алгоритму подбирать сложность)
    target_score = Column(Integer, default=80) 

class Topic(Base):
    """Глобальные темы, соответствующие номерам заданий из КИМ ЕГЭ"""
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    ege_task_number = Column(Integer, nullable=False) # От 1 до 19
    name = Column(String, nullable=False) # Например: "Планиметрия", "Экономическая задача"
    is_part_two = Column(Boolean, default=False) # Флаг для второй части (задания 13-19)

class MicroSkill(Base):
    """Узлы графа: микронавыки, из которых состоит задание"""
    __tablename__ = "micro_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # Например: "Площадь сечения конуса"
    topic_id = Column(Integer, ForeignKey("topics.id"))
    
    topic = relationship("Topic")

class Question(Base):
    """База тренировочных задач"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False) # Текст задачи (может содержать LaTeX)
    image_url = Column(String, nullable=True) # Ссылка на картинку (важно для графиков производных!)
    correct_answer = Column(String, nullable=False)
    difficulty = Column(Integer, default=1) # Сложность от 1 до 5
    
    micro_skill_id = Column(Integer, ForeignKey("micro_skills.id"))
    micro_skill = relationship("MicroSkill")

class UserSkillMastery(Base):
    """Тепловая карта: прогресс ученика"""
    __tablename__ = "user_skill_mastery"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    micro_skill_id = Column(Integer, ForeignKey("micro_skills.id"))
    
    mastery_percentage = Column(Float, default=0.0) # Процент владения от 0 до 100

class SpacedRepetition(Base):
    """Интервальное повторение (Алгоритм SM-2)"""
    __tablename__ = "spaced_repetition"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    micro_skill_id = Column(Integer, ForeignKey("micro_skills.id"))
    
    next_review = Column(DateTime, default=datetime.datetime.utcnow)
    interval = Column(Integer, default=1) 
    ease_factor = Column(Float, default=2.5)

class AnswerLog(Base):
    """История ответов для аналитики (детектора списывания и репетитора)"""
    __tablename__ = "answer_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    is_correct = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)