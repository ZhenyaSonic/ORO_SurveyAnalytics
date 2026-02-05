from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import Base


class Respondent(Base):
    __tablename__ = "respondents"

    id = Column(String(100), primary_key=True, index=True)
    
    # Relationships
    text_responses = relationship("TextResponse", back_populates="respondent")
    choice_responses = relationship("ChoiceResponse", back_populates="respondent")

