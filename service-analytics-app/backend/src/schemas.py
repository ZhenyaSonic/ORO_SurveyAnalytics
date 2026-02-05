"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class QuestionTypeEnum(str, Enum):
    TEXT = "TEXT"
    SINGLE = "SINGLE"
    MULTIPLE = "MULTIPLE"


class SurveyBase(BaseModel):
    id: str


class Survey(SurveyBase):
    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    id: str
    name: str
    text: str
    type: QuestionTypeEnum


class Question(QuestionBase):
    survey_id: str

    class Config:
        from_attributes = True


class AnswerOptionBase(BaseModel):
    id: str
    code: int
    label: str


class AnswerOption(AnswerOptionBase):
    question_id: str

    class Config:
        from_attributes = True


class RespondentResponse(BaseModel):
    respondent_id: str
    responses: Dict[str, Any]


class ValidateQuestionsRequest(BaseModel):
    survey_id: str
    question_ids: List[str]


class ValidateQuestionsResponse(BaseModel):
    valid: bool
    errors: List[str] = []


class GetResponsesRequest(BaseModel):
    survey_id: str
    question_ids: List[str]


class ResponseData(BaseModel):
    question_id: str
    question_name: str
    question_type: str
    value: Any


class RespondentResponseData(BaseModel):
    respondent_id: str
    responses: List[ResponseData]


class GetResponsesResponse(BaseModel):
    respondents: List[RespondentResponseData]
