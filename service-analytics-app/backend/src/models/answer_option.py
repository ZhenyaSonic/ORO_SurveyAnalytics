from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id = Column(String(100), primary_key=True, index=True)
    question_id = Column(String(100), ForeignKey("questions.id"), nullable=False)
    code = Column(Integer, nullable=False)
    label = Column(String(500), nullable=False)

    question = relationship("Question", back_populates="answer_options")
    choice_responses = relationship("ChoiceResponse", back_populates="answer_option")
