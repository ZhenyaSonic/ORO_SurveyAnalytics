"""
Survey-related business logic.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException
from src.models import Survey, Question, QuestionType
from src.schemas import (
    Survey as SurveySchema,
    Question as QuestionSchema,
    ValidateQuestionsRequest,
    ValidateQuestionsResponse,
)
from src.logger import logger


class SurveyService:
    """Service for survey-related operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_surveys(self) -> List[SurveySchema]:
        """Get all surveys."""
        surveys = self.db.query(Survey).all()
        return [SurveySchema.model_validate(s) for s in surveys]

    def get_survey_questions(self, survey_id: str) -> List[QuestionSchema]:
        """Get all questions for a survey."""
        survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        questions = self.db.query(Question).filter(Question.survey_id == survey_id).all()

        result = []
        for q in questions:
            type_map = {
                QuestionType.TEXT: "TEXT",
                QuestionType.SINGLE: "SINGLE",
                QuestionType.MULTIPLE: "MULTIPLE"
            }
            result.append(QuestionSchema(
                id=q.id,
                survey_id=q.survey_id,
                name=q.name,
                text=q.text,
                type=type_map.get(q.type, "TEXT")
            ))
        return result

    def validate_questions(self, request: ValidateQuestionsRequest) -> ValidateQuestionsResponse:
        """Validate that question IDs (by name) belong to the specified survey."""
        survey = self.db.query(Survey).filter(Survey.id == request.survey_id).first()
        if not survey:
            return ValidateQuestionsResponse(
                valid=False, 
                errors=[f"Survey {request.survey_id} not found"]
            )

        survey_questions = self.db.query(Question.id, Question.name).filter(
            Question.survey_id == request.survey_id
        ).all()

        question_name_to_id = {q.name: q.id for q in survey_questions}
        valid_question_names = set(question_name_to_id.keys())

        errors = []
        for q_name in request.question_ids:
            if q_name not in valid_question_names:
                errors.append(f"Question {q_name} not found in survey {request.survey_id}")

        return ValidateQuestionsResponse(valid=len(errors) == 0, errors=errors)

    def get_survey_by_id(self, survey_id: str) -> Optional[Survey]:
        """Get survey by ID."""
        return self.db.query(Survey).filter(Survey.id == survey_id).first()
