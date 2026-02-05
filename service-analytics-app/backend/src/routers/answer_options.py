"""
API routes for answer options (for tooltips with codes and labels).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from src.models import get_db, AnswerOption, Question
from src.schemas import AnswerOption as AnswerOptionSchema

router = APIRouter(prefix="/api/answer-options", tags=["answer-options"])


@router.get("/question/{question_id}", response_model=List[AnswerOptionSchema])
def get_answer_options_for_question(question_id: str, db: Session = Depends(get_db)):
    """Get all answer options for a specific question."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    answer_options = db.query(AnswerOption).filter(
        AnswerOption.question_id == question_id
    ).order_by(AnswerOption.code).all()
    
    return [AnswerOptionSchema.model_validate(ao) for ao in answer_options]


@router.get("/questions/{question_ids_str}", response_model=Dict[str, List[AnswerOptionSchema]])
def get_answer_options_for_questions(question_ids_str: str, db: Session = Depends(get_db)):
    """Get answer options for multiple questions. question_ids_str is comma-separated."""
    question_ids = [qid.strip() for qid in question_ids_str.split(",")]
    
    answer_options = db.query(AnswerOption).filter(
        AnswerOption.question_id.in_(question_ids)
    ).order_by(AnswerOption.question_id, AnswerOption.code).all()
    
    # Group by question_id
    result: Dict[str, List[AnswerOptionSchema]] = {}
    for ao in answer_options:
        if ao.question_id not in result:
            result[ao.question_id] = []
        result[ao.question_id].append(AnswerOptionSchema.model_validate(ao))
    
    return result

