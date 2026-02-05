"""
API routes for surveys and responses.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from src.models import get_db, Survey, Question, QuestionType
from src.schemas import (
    Survey as SurveySchema,
    Question as QuestionSchema,
    ValidateQuestionsRequest,
    ValidateQuestionsResponse,
    GetResponsesRequest,
    GetResponsesResponse,
    RespondentResponseData,
    ResponseData,
)
from src.logger import logger
from src.services.survey_service import SurveyService
from src.services.response_service import ResponseService

router = APIRouter(prefix="/api/surveys", tags=["surveys"])


@router.get("/", response_model=List[SurveySchema])
def get_surveys(db: Session = Depends(get_db)) -> List[SurveySchema]:
    """Get all surveys."""
    survey_service = SurveyService(db)
    return survey_service.get_all_surveys()


@router.get("/{survey_id}/questions", response_model=List[QuestionSchema])
def get_survey_questions(survey_id: str, db: Session = Depends(get_db)) -> List[QuestionSchema]:
    """Get all questions for a survey."""
    survey_service = SurveyService(db)
    return survey_service.get_survey_questions(survey_id)


@router.post("/validate-questions", response_model=ValidateQuestionsResponse)
def validate_questions(
    request: ValidateQuestionsRequest, 
    db: Session = Depends(get_db)
) -> ValidateQuestionsResponse:
    """Validate that question IDs (by name) belong to the specified survey."""
    survey_service = SurveyService(db)
    return survey_service.validate_questions(request)


@router.post("/responses", response_model=GetResponsesResponse)
def get_responses(
    request: GetResponsesRequest,
    db: Session = Depends(get_db)
) -> GetResponsesResponse:
    """Get responses for specified questions (by name) in a survey."""
    logger.debug(f"=== Request for survey {request.survey_id}, questions: {request.question_ids} ===")

    response_service = ResponseService(db)
    return response_service.get_responses_for_questions(request)


@router.get("/{survey_id}/all-responses", response_model=GetResponsesResponse)
def get_all_responses(survey_id: str, db: Session = Depends(get_db)) -> GetResponsesResponse:
    """Get all responses for all questions in a survey."""
    survey_service = SurveyService(db)
    questions = survey_service.get_survey_questions(survey_id)

    if not questions:
        return GetResponsesResponse(respondents=[])

    request = GetResponsesRequest(
        survey_id=survey_id,
        question_ids=[q.name for q in questions]
    )

    response_service = ResponseService(db)
    return response_service.get_responses_for_questions(request)
