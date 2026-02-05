from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class TextResponse(Base):
    __tablename__ = "text_responses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    respondent_id = Column(String(100), ForeignKey("respondents.id"), nullable=False)
    question_id = Column(String(100), ForeignKey("questions.id"), nullable=False)
    survey_id = Column(String(50), ForeignKey("surveys.id"), nullable=False)
    text = Column(Text, nullable=False)

    respondent = relationship("Respondent", back_populates="text_responses")
    question = relationship("Question", back_populates="text_responses")
    survey = relationship("Survey", back_populates="text_responses")


class ChoiceResponse(Base):
    __tablename__ = "choice_responses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    respondent_id = Column(String(100), ForeignKey("respondents.id"), nullable=False)
    question_id = Column(String(100), ForeignKey("questions.id"), nullable=False)
    survey_id = Column(String(50), ForeignKey("surveys.id"), nullable=False)
    answer_option_id = Column(String(100), ForeignKey("answer_options.id"), nullable=False)
    response_order = Column(Integer, default=1)

    respondent = relationship("Respondent", back_populates="choice_responses")
    question = relationship("Question", back_populates="choice_responses")
    answer_option = relationship("AnswerOption", back_populates="choice_responses")
    survey = relationship("Survey", back_populates="choice_responses")
