from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import Base


class Survey(Base):
    __tablename__ = "surveys"

    id = Column(String(50), primary_key=True, index=True)
    
    # Relationships
    questions = relationship("Question", back_populates="survey", cascade="all, delete-orphan")
    text_responses = relationship("TextResponse", back_populates="survey")
    choice_responses = relationship("ChoiceResponse", back_populates="survey")

