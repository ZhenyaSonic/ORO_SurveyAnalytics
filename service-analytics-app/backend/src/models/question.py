from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum
import enum
from sqlalchemy.orm import relationship
from .base import Base


class QuestionType(enum.Enum):
    TEXT = 1
    SINGLE = 2
    MULTIPLE = 3


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(100), primary_key=True, index=True)
    survey_id = Column(String(50), ForeignKey("surveys.id"), nullable=False)
    name = Column(String(200), nullable=False)
    text = Column(String(1000), nullable=False)
    type = Column(SQLEnum(QuestionType), nullable=False)

    # Relationships
    survey = relationship("Survey", back_populates="questions")
    answer_options = relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan")
    text_responses = relationship("TextResponse", back_populates="question")
    choice_responses = relationship("ChoiceResponse", back_populates="question")

