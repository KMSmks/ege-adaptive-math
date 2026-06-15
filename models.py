import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=True) 
    
    target_score = Column(Integer, default=80) 

class Topic(Base):
    """Глобальные темы, соответствующие номерам заданий из КИМ ЕГЭ"""
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    ege_task_number = Column(Integer, nullable=False) 
    name = Column(String, nullable=False) 
    is_part_two = Column(Boolean, default=False) 

class MicroSkill(Base):
    """Узлы графа: микронавыки, из которых состоит задание"""
    __tablename__ = "micro_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) 
    topic_id = Column(Integer, ForeignKey("topics.id"))
    
    topic = relationship("Topic")

class Question(Base):
    """База тренировочных задач"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False) 
    image_url = Column(String, nullable=True) 
    correct_answer = Column(String, nullable=False)
    
    
    solution = Column(String, nullable=True)
    difficulty = Column(Integer, default=1) 
    
    micro_skill_id = Column(Integer, ForeignKey("micro_skills.id"))
    micro_skill = relationship("MicroSkill")

class UserSkillMastery(Base):
    """Тепловая карта: прогресс ученика"""
    __tablename__ = "user_skill_mastery"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    micro_skill_id = Column(Integer, ForeignKey("micro_skills.id"))
    
    mastery_percentage = Column(Float, default=0.0) 

class SpacedRepetition(Base):
    """Интервальное повторение (Алгоритм SM-2)"""
    __tablename__ = "spaced_repetition"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    micro_skill_id = Column(Integer, ForeignKey("micro_skills.id"))
    
    next_review = Column(DateTime, default=datetime.datetime.utcnow)
    interval = Column(Integer, default=1) 
    ease_factor = Column(Float, default=2.5)
    
    repetitions = Column(Integer, default=0)

class AnswerLog(Base):
    """История ответов для аналитики (детектора списывания и репетитора)"""
    __tablename__ = "answer_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    is_correct = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)