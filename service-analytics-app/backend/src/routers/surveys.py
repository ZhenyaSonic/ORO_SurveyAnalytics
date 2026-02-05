"""
API routes for surveys and responses.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.models import get_db, Survey, Question, Respondent, TextResponse, ChoiceResponse, AnswerOption, QuestionType
from src.schemas import (
    Survey as SurveySchema,
    Question as QuestionSchema,
    ValidateQuestionsRequest,
    ValidateQuestionsResponse,
    GetResponsesRequest,
    GetResponsesResponse,
    RespondentResponseData,
    ResponseData,
    QuestionTypeEnum
)

router = APIRouter(prefix="/api/surveys", tags=["surveys"])


@router.get("/", response_model=List[SurveySchema])
def get_surveys(db: Session = Depends(get_db)):
    """Get all surveys."""
    surveys = db.query(Survey).all()
    return surveys


@router.get("/debug/{survey_id}/questions")
def get_survey_questions_debug(survey_id: str, db: Session = Depends(get_db)):
    """Debug endpoint to see questions for a survey"""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        return {"error": f"Survey {survey_id} not found"}
    
    questions = db.query(Question).filter(Question.survey_id == survey_id).all()
    return {
        "survey_id": survey_id,
        "question_count": len(questions),
        "questions": [
            {
                "id": q.id,
                "name": q.name,
                "type": str(q.type)
            }
            for q in questions
        ]
    }

@router.get("/{survey_id}/questions", response_model=List[QuestionSchema])
def get_survey_questions(survey_id: str, db: Session = Depends(get_db)):
    """Get all questions for a survey."""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    questions = db.query(Question).filter(Question.survey_id == survey_id).all()
    # Convert QuestionType enum to string for response
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


@router.post("/validate-questions", response_model=ValidateQuestionsResponse)
def validate_questions(request: ValidateQuestionsRequest, db: Session = Depends(get_db)):
    """Validate that question IDs belong to the specified survey."""
    survey = db.query(Survey).filter(Survey.id == request.survey_id).first()
    if not survey:
        return ValidateQuestionsResponse(valid=False, errors=[f"Survey {request.survey_id} not found"])
    
    # Get all question IDs for this survey
    survey_questions = db.query(Question.id).filter(Question.survey_id == request.survey_id).all()
    valid_question_ids = {q.id for q in survey_questions}
    
    errors = []
    for q_id in request.question_ids:
        if q_id not in valid_question_ids:
            errors.append(f"Question {q_id} not found in survey {request.survey_id}")
    
    return ValidateQuestionsResponse(valid=len(errors) == 0, errors=errors)


@router.post("/responses", response_model=GetResponsesResponse)
def get_responses(request: GetResponsesRequest, db: Session = Depends(get_db)):
    """Get responses for specified questions in a survey."""
    # Validate survey exists
    survey = db.query(Survey).filter(Survey.id == request.survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Get questions with their types
    questions = db.query(Question).filter(
        Question.survey_id == request.survey_id,
        Question.id.in_(request.question_ids)
    ).all()
    
    question_map = {q.id: q for q in questions}
    
    # Get all respondents for this survey
    text_responses = db.query(TextResponse).filter(
        TextResponse.survey_id == request.survey_id,
        TextResponse.question_id.in_(request.question_ids)
    ).all()
    
    choice_responses = db.query(ChoiceResponse).filter(
        ChoiceResponse.survey_id == request.survey_id,
        ChoiceResponse.question_id.in_(request.question_ids)
    ).all()
    
    # Group responses by respondent
    respondent_data: Dict[str, Dict[str, Any]] = {}
    
    # Process text responses
    for tr in text_responses:
        if tr.respondent_id not in respondent_data:
            respondent_data[tr.respondent_id] = {}
        if tr.question_id not in respondent_data[tr.respondent_id]:
            respondent_data[tr.respondent_id][tr.question_id] = {
                "question_id": tr.question_id,
                "question_name": question_map[tr.question_id].name if tr.question_id in question_map else "",
                "question_type": "TEXT",
                "value": tr.text
            }
    
    # Process choice responses
    for cr in choice_responses:
        if cr.respondent_id not in respondent_data:
            respondent_data[cr.respondent_id] = {}
        
        question = question_map.get(cr.question_id)
        if not question:
            continue
        
        # Get answer option details
        answer_option = db.query(AnswerOption).filter(
            AnswerOption.id == cr.answer_option_id
        ).first()
        
        if not answer_option:
            continue
        
        if cr.question_id not in respondent_data[cr.respondent_id]:
            # Initialize with empty list
            respondent_data[cr.respondent_id][cr.question_id] = {
                "question_id": cr.question_id,
                "question_name": question.name,
                "question_type": "SINGLE" if question.type == QuestionType.SINGLE else "MULTIPLE",
                "value": []
            }
        
        # Add code to the list, maintaining order
        codes = respondent_data[cr.respondent_id][cr.question_id]["value"]
        if isinstance(codes, list):
            # Store as tuple (order, code) for sorting
            codes.append((cr.response_order, answer_option.code))
            # Sort by order and extract codes (remove duplicates by code, keep first occurrence)
            seen_codes = set()
            codes_sorted = []
            for order, code in sorted(codes, key=lambda x: x[0]):
                if code not in seen_codes:
                    codes_sorted.append(code)
                    seen_codes.add(code)
            respondent_data[cr.respondent_id][cr.question_id]["value"] = codes_sorted
    
    # Convert to response format
    respondents_list = []
    for respondent_id, responses_dict in respondent_data.items():
        # Ensure all requested questions are present
        responses_list = []
        for q_id in request.question_ids:
            if q_id in responses_dict:
                responses_list.append(ResponseData(**responses_dict[q_id]))
            else:
                # Question with no response
                question = question_map.get(q_id)
                if question:
                    question_type_str = "TEXT" if question.type == QuestionType.TEXT else \
                                      "SINGLE" if question.type == QuestionType.SINGLE else "MULTIPLE"
                    responses_list.append(ResponseData(
                        question_id=q_id,
                        question_name=question.name,
                        question_type=question_type_str,
                        value="" if question.type == QuestionType.TEXT else []
                    ))
        
        respondents_list.append(RespondentResponseData(
            respondent_id=respondent_id,
            responses=responses_list
        ))
    
    return GetResponsesResponse(respondents=respondents_list)


@router.get("/{survey_id}/all-responses", response_model=GetResponsesResponse)
def get_all_responses(survey_id: str, db: Session = Depends(get_db)):
    """Get all responses for all questions in a survey."""
    # Get all questions for this survey
    questions = db.query(Question).filter(Question.survey_id == survey_id).all()
    question_ids = [q.id for q in questions]
    
    if not question_ids:
        return GetResponsesResponse(respondents=[])
    
    request = GetResponsesRequest(survey_id=survey_id, question_ids=question_ids)
    return get_responses(request, db)

