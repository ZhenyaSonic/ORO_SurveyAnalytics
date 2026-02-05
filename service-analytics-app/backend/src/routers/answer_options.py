"""
API routes for answer options (for tooltips with codes and labels).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from src.models import get_db, AnswerOption, Question
from src.schemas import AnswerOption as AnswerOptionSchema
from logger import logger

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
    """Get answer options for multiple questions. question_ids_str can be names (Q1, Q2) or UUIDs."""
    question_ids = [qid.strip() for qid in question_ids_str.split(",")]

    logger.debug(f"DEBUG: Looking for answer options for: {question_ids}")

    questions_by_name = db.query(Question).filter(Question.name.in_(question_ids)).all()

    if questions_by_name:
        question_uuids = [q.id for q in questions_by_name]
        logger.debug(f"DEBUG: Found questions by name, UUIDs: {question_uuids}")
        answer_options = db.query(AnswerOption).filter(
            AnswerOption.question_id.in_(question_uuids)
        ).order_by(AnswerOption.question_id, AnswerOption.code).all()
    else:
        logger.debug(f"DEBUG: No questions found by name, trying by UUID")
        answer_options = db.query(AnswerOption).filter(
            AnswerOption.question_id.in_(question_ids)
        ).order_by(AnswerOption.question_id, AnswerOption.code).all()

    logger.debug(f"DEBUG: Found {len(answer_options)} answer options")

    result_by_uuid: Dict[str, List[AnswerOptionSchema]] = {}
    for ao in answer_options:
        if ao.question_id not in result_by_uuid:
            result_by_uuid[ao.question_id] = []
        result_by_uuid[ao.question_id].append(AnswerOptionSchema.model_validate(ao))

    result_by_name: Dict[str, List[AnswerOptionSchema]] = {}

    all_question_ids = list(result_by_uuid.keys())
    if all_question_ids:
        questions = db.query(Question.id, Question.name).filter(Question.id.in_(all_question_ids)).all()
        question_id_to_name = {q.id: q.name for q in questions}

        for question_uuid, options in result_by_uuid.items():
            question_name = question_id_to_name.get(question_uuid, question_uuid)
            result_by_name[question_name] = options

    logger.debug(f"DEBUG: Result by name: {list(result_by_name.keys())}")
    return result_by_name
