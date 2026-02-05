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
from src.logger import logger

router = APIRouter(prefix="/api/surveys", tags=["surveys"])


@router.get("/", response_model=List[SurveySchema])
def get_surveys(db: Session = Depends(get_db)):
    """Get all surveys."""
    surveys = db.query(Survey).all()
    return surveys


@router.get("/{survey_id}/questions", response_model=List[QuestionSchema])
def get_survey_questions(survey_id: str, db: Session = Depends(get_db)):
    """Get all questions for a survey."""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    questions = db.query(Question).filter(Question.survey_id == survey_id).all()

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
    """Validate that question IDs (by name) belong to the specified survey."""
    survey = db.query(Survey).filter(Survey.id == request.survey_id).first()
    if not survey:
        return ValidateQuestionsResponse(valid=False, errors=[f"Survey {request.survey_id} not found"])

    survey_questions = db.query(Question.id, Question.name).filter(Question.survey_id == request.survey_id).all()

    question_name_to_id = {q.name: q.id for q in survey_questions}
    valid_question_names = set(question_name_to_id.keys())

    errors = []
    for q_name in request.question_ids:
        if q_name not in valid_question_names:
            errors.append(f"Question {q_name} not found in survey {request.survey_id}")

    return ValidateQuestionsResponse(valid=len(errors) == 0, errors=errors)


@router.post("/responses", response_model=GetResponsesResponse)
def get_responses(request: GetResponsesRequest, db: Session = Depends(get_db)):
    """Get responses for specified questions (by name) in a survey."""
    logger.debug(f"=== DEBUG START: Request for survey {request.survey_id}, questions: {request.question_ids} ===")

    survey = db.query(Survey).filter(Survey.id == request.survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    questions = db.query(Question).filter(
        Question.survey_id == request.survey_id,
        Question.name.in_(request.question_ids)
    ).all()

    logger.debug(f"DEBUG: Found {len(questions)} questions by name")
    for q in questions:
        logger.info(f"  - {q.name} (ID: {q.id}, Type: {q.type})")

    question_name_map = {q.name: q for q in questions}

    not_found = [q_name for q_name in request.question_ids if q_name not in question_name_map]
    if not_found:
        raise HTTPException(
            status_code=400,
            detail=f"Questions not found in survey: {', '.join(not_found)}"
        )

    question_uuids = [q.id for q in questions]

    text_responses = db.query(TextResponse).filter(
        TextResponse.survey_id == request.survey_id,
        TextResponse.question_id.in_(question_uuids)
    ).all()

    choice_responses = db.query(ChoiceResponse).filter(
        ChoiceResponse.survey_id == request.survey_id,
        ChoiceResponse.question_id.in_(question_uuids)
    ).all()

    logger.debug(f"DEBUG: Found {len(text_responses)} text responses and {len(choice_responses)} choice responses")

    respondent_data: Dict[str, Dict[str, Any]] = {}

    for tr in text_responses:
        if tr.respondent_id not in respondent_data:
            respondent_data[tr.respondent_id] = {}

        question = next((q for q in questions if q.id == tr.question_id), None)
        if not question:
            continue

        question_name = question.name

        if question_name not in respondent_data[tr.respondent_id]:
            respondent_data[tr.respondent_id][question_name] = {
                "question_id": question_name,
                "question_name": question.name,
                "question_type": "TEXT",
                "value": tr.text
            }

    for cr in choice_responses:
        if cr.respondent_id not in respondent_data:
            respondent_data[cr.respondent_id] = {}

        question = next((q for q in questions if q.id == cr.question_id), None)
        if not question:
            continue

        question_name = question.name

        answer_option = db.query(AnswerOption).filter(
            AnswerOption.id == cr.answer_option_id
        ).first()

        if not answer_option:
            continue

        logger.debug(
            f"DEBUG - Processing: respondent={cr.respondent_id}, question={question_name}, "
            f"type={question.type}, code={answer_option.code}"
        )

        if question_name not in respondent_data[cr.respondent_id]:
            question_type_str = "SINGLE" if question.type == QuestionType.SINGLE else "MULTIPLE"

            initial_value = [] if question.type == QuestionType.MULTIPLE else None

            respondent_data[cr.respondent_id][question_name] = {
                "question_id": question_name,
                "question_name": question.name,
                "question_type": question_type_str,
                "value": initial_value
            }

        current_response = respondent_data[cr.respondent_id][question_name]

        if question.type == QuestionType.SINGLE:

            current_response["value"] = answer_option.code
            logger.debug(f"DEBUG - Set SINGLE value: {question_name} = {answer_option.code}")
        else:
            if not isinstance(current_response["value"], list):
                current_response["value"] = []

            if "_orders" not in current_response:
                current_response["_orders"] = []

            current_response["_orders"].append((cr.response_order, answer_option.code))

    for respondent_id, responses_dict in respondent_data.items():
        for question_name, response_data in responses_dict.items():
            if response_data.get("question_type") == "MULTIPLE" and "_orders" in response_data:
                order_info = response_data["_orders"]
                seen_codes = set()
                sorted_codes = []

                for order, code in sorted(order_info, key=lambda x: x[0]):
                    if code not in seen_codes:
                        sorted_codes.append(code)
                        seen_codes.add(code)

                response_data["value"] = sorted_codes
                del response_data["_orders"]

    respondents_list = []
    for respondent_id, responses_dict in respondent_data.items():

        responses_list = []
        for q_name in request.question_ids:
            if q_name in responses_dict:
                response_data = responses_dict[q_name].copy()

                if response_data["question_type"] == "SINGLE":
                    if response_data["value"] is None:
                        response_data["value"] = ""
                        logger.warning(f"DEBUG - WARNING: SINGLE question {q_name} has None value for respondent {respondent_id}")

                clean_data = {
                    "question_id": response_data["question_id"],
                    "question_name": response_data["question_name"],
                    "question_type": response_data["question_type"],
                    "value": response_data["value"]
                }
                responses_list.append(ResponseData(**clean_data))
            else:
                question = question_name_map.get(q_name)
                if question:
                    question_type_str = "TEXT" if question.type == QuestionType.TEXT else \
                                      "SINGLE" if question.type == QuestionType.SINGLE else "MULTIPLE"
                    default_value = "" if question.type == QuestionType.TEXT else \
                                   "" if question.type == QuestionType.SINGLE else []

                    responses_list.append(ResponseData(
                        question_id=q_name,
                        question_name=question.name,
                        question_type=question_type_str,
                        value=default_value
                    ))

        respondents_list.append(RespondentResponseData(
            respondent_id=respondent_id,
            responses=responses_list
        ))

    logger.debug(f"\n=== DEBUG: SAMPLE RESPONSE DATA ===")
    if respondents_list:
        sample = respondents_list[0]
        logger.info(f"First respondent: {sample.respondent_id}")
        for resp in sample.responses:
            logger.info(f"  - {resp.question_name} ({resp.question_type}): {resp.value} (type: {type(resp.value)})")

    logger.debug(f"=== DEBUG END: Returning data for {len(respondents_list)} respondents ===")
    return GetResponsesResponse(respondents=respondents_list)


@router.get("/{survey_id}/all-responses", response_model=GetResponsesResponse)
def get_all_responses(survey_id: str, db: Session = Depends(get_db)):
    """Get all responses for all questions in a survey."""
    questions = db.query(Question).filter(Question.survey_id == survey_id).all()
    question_ids = [q.id for q in questions]

    if not question_ids:
        return GetResponsesResponse(respondents=[])

    request = GetResponsesRequest(survey_id=survey_id, question_ids=question_ids)
    return get_responses(request, db)
