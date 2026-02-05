"""
Response-related business logic.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
from src.models import (
    Survey, Question, QuestionType,
    TextResponse, ChoiceResponse, AnswerOption
)
from src.schemas import (
    GetResponsesRequest,
    GetResponsesResponse,
    RespondentResponseData,
    ResponseData,
)
from src.logger import logger


class ResponseDataBuilder:
    """Helper class for building response data."""

    @staticmethod
    def build_single_choice_value(
        question_name: str,
        question_type: str,
        answer_option: Optional[AnswerOption]
    ) -> Any:
        """Build value for single choice question."""
        if answer_option:
            return answer_option.code
        logger.warning(f"DEBUG - WARNING: SINGLE question {question_name} has None value")
        return ""

    @staticmethod
    def build_multiple_choice_values(
        choice_responses_for_question: List[ChoiceResponse],
        db: Session
    ) -> List[int]:
        """Build values for multiple choice question from ChoiceResponse objects."""
        codes_with_orders = []

        for cr in choice_responses_for_question:
            answer_option = db.query(AnswerOption).filter(
                AnswerOption.id == cr.answer_option_id
            ).first()

            if answer_option:
                codes_with_orders.append((cr.response_order, answer_option.code))

        return ResponseDataBuilder._process_multiple_choice_orders(codes_with_orders)

    @staticmethod
    def build_multiple_choice_values_from_orders(order_info: List[Tuple[int, int]]) -> List[int]:
        """Build values for multiple choice question from order information."""
        return ResponseDataBuilder._process_multiple_choice_orders(order_info)

    @staticmethod
    def _process_multiple_choice_orders(codes_with_orders: List[Tuple[int, int]]) -> List[int]:
        """Process multiple choice orders to sort and deduplicate."""
        seen_codes = set()
        sorted_codes = []

        for order, code in sorted(codes_with_orders, key=lambda x: x[0]):
            if code not in seen_codes:
                sorted_codes.append(code)
                seen_codes.add(code)

        return sorted_codes

    @staticmethod
    def get_default_value_for_question(question_type: QuestionType) -> Any:
        """Get default value based on question type."""
        if question_type == QuestionType.TEXT:
            return ""
        elif question_type == QuestionType.SINGLE:
            return ""
        else:
            return []


class ResponseService:
    """Service for response-related operations."""

    def __init__(self, db: Session):
        self.db = db
        self.data_builder = ResponseDataBuilder()

    def get_responses_for_questions(self, request: GetResponsesRequest) -> GetResponsesResponse:
        """Get responses for specified questions (by name) in a survey."""

        survey = self.db.query(Survey).filter(Survey.id == request.survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        questions = self.db.query(Question).filter(
            Question.survey_id == request.survey_id,
            Question.name.in_(request.question_ids)
        ).all()

        logger.debug(f"DEBUG: Found {len(questions)} questions by name")

        question_name_map = {q.name: q for q in questions}
        not_found = [q_name for q_name in request.question_ids if q_name not in question_name_map]
        if not_found:
            raise HTTPException(
                status_code=400,
                detail=f"Questions not found in survey: {', '.join(not_found)}"
            )

        respondent_data = self._process_responses(questions)

        respondents_list = self._build_respondents_list(
            respondent_data,
            request.question_ids,
            question_name_map
        )

        self._log_sample_response(respondents_list)

        return GetResponsesResponse(respondents=respondents_list)

    def _process_responses(self, questions: List[Question]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Process text and choice responses for questions."""
        if not questions:
            return {}

        question_uuids = [q.id for q in questions]
        survey_id = questions[0].survey_id

        text_responses = self.db.query(TextResponse).filter(
            TextResponse.survey_id == survey_id,
            TextResponse.question_id.in_(question_uuids)
        ).all()

        choice_responses = self.db.query(ChoiceResponse).filter(
            ChoiceResponse.survey_id == survey_id,
            ChoiceResponse.question_id.in_(question_uuids)
        ).all()

        logger.debug(f"DEBUG: Found {len(text_responses)} text responses and {len(choice_responses)} choice responses")

        respondent_data: Dict[str, Dict[str, Dict[str, Any]]] = {}

        self._process_text_responses(text_responses, questions, respondent_data)

        self._process_choice_responses(choice_responses, questions, respondent_data)

        self._post_process_multiple_choice_responses(respondent_data)

        return respondent_data

    def _process_text_responses(
        self,
        text_responses: List[TextResponse],
        questions: List[Question],
        respondent_data: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> None:
        """Process text responses."""
        for tr in text_responses:
            respondent_id = tr.respondent_id
            if respondent_id not in respondent_data:
                respondent_data[respondent_id] = {}

            question = next((q for q in questions if q.id == tr.question_id), None)
            if not question:
                continue

            question_name = question.name

            if question_name not in respondent_data[respondent_id]:
                respondent_data[respondent_id][question_name] = {
                    "question_id": question_name,
                    "question_name": question.name,
                    "question_type": "TEXT",
                    "value": tr.text
                }

    def _process_choice_responses(
        self,
        choice_responses: List[ChoiceResponse],
        questions: List[Question],
        respondent_data: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> None:
        """Process choice responses."""
        for cr in choice_responses:
            respondent_id = cr.respondent_id
            if respondent_id not in respondent_data:
                respondent_data[respondent_id] = {}

            question = next((q for q in questions if q.id == cr.question_id), None)
            if not question:
                continue

            question_name = question.name
            answer_option = self.db.query(AnswerOption).filter(
                AnswerOption.id == cr.answer_option_id
            ).first()

            if not answer_option:
                continue

            logger.debug(
                f"DEBUG - Processing: respondent={respondent_id}, question={question_name}, "
                f"type={question.type}, code={answer_option.code}"
            )

            if question_name not in respondent_data[respondent_id]:
                question_type_str = "SINGLE" if question.type == QuestionType.SINGLE else "MULTIPLE"
                initial_value = [] if question.type == QuestionType.MULTIPLE else None

                respondent_data[respondent_id][question_name] = {
                    "question_id": question_name,
                    "question_name": question.name,
                    "question_type": question_type_str,
                    "value": initial_value,
                    "_orders": [] if question.type == QuestionType.MULTIPLE else None
                }

            current_response = respondent_data[respondent_id][question_name]

            if question.type == QuestionType.SINGLE:
                current_response["value"] = answer_option.code
                logger.debug(f"DEBUG - Set SINGLE value: {question_name} = {answer_option.code}")
            else:
                if "_orders" in current_response and current_response["_orders"] is not None:
                    current_response["_orders"].append((cr.response_order, answer_option.code))

    def _post_process_multiple_choice_responses(
        self,
        respondent_data: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> None:
        """Post-process multiple choice responses to order and deduplicate."""
        for respondent_id, responses_dict in respondent_data.items():
            for question_name, response_data in responses_dict.items():
                if response_data.get("question_type") == "MULTIPLE" and "_orders" in response_data:
                    order_info = response_data["_orders"]
                    if order_info:
                        sorted_codes = self.data_builder.build_multiple_choice_values_from_orders(order_info)
                        response_data["value"] = sorted_codes
                    del response_data["_orders"]

    def _build_respondents_list(
        self,
        respondent_data: Dict[str, Dict[str, Dict[str, Any]]],
        requested_question_ids: List[str],
        question_name_map: Dict[str, Question]
    ) -> List[RespondentResponseData]:
        """Build list of RespondentResponseData objects."""
        respondents_list = []

        for respondent_id, responses_dict in respondent_data.items():
            responses_list = self._build_responses_for_respondent(
                respondent_id, responses_dict, requested_question_ids, question_name_map
            )

            respondents_list.append(RespondentResponseData(
                respondent_id=respondent_id,
                responses=responses_list
            ))

        return respondents_list

    def _build_responses_for_respondent(
        self,
        respondent_id: str,
        responses_dict: Dict[str, Dict[str, Any]],
        requested_question_ids: List[str],
        question_name_map: Dict[str, Question]
    ) -> List[ResponseData]:
        """Build responses for a single respondent."""
        responses_list = []

        for q_name in requested_question_ids:
            if q_name in responses_dict:
                response_data = responses_dict[q_name].copy()
                clean_data = self._clean_response_data(response_data, respondent_id, q_name)
                responses_list.append(ResponseData(**clean_data))
            else:
                question = question_name_map.get(q_name)
                if question:
                    default_value = self.data_builder.get_default_value_for_question(question.type)
                    question_type_str = self._get_question_type_string(question.type)

                    responses_list.append(ResponseData(
                        question_id=q_name,
                        question_name=question.name,
                        question_type=question_type_str,
                        value=default_value
                    ))

        return responses_list

    def _clean_response_data(
        self,
        response_data: Dict[str, Any],
        respondent_id: str,
        question_name: str
    ) -> Dict[str, Any]:
        """Clean and validate response data."""
        if response_data["question_type"] == "SINGLE" and response_data["value"] is None:
            response_data["value"] = ""
            logger.warning(f"DEBUG - WARNING: SINGLE question {question_name} has None value for respondent {respondent_id}")

        return {
            "question_id": response_data["question_id"],
            "question_name": response_data["question_name"],
            "question_type": response_data["question_type"],
            "value": response_data["value"]
        }

    def _get_question_type_string(self, question_type: QuestionType) -> str:
        """Convert QuestionType enum to string."""
        if question_type == QuestionType.TEXT:
            return "TEXT"
        elif question_type == QuestionType.SINGLE:
            return "SINGLE"
        else:
            return "MULTIPLE"

    def _log_sample_response(self, respondents_list: List[RespondentResponseData]) -> None:
        """Log sample response for debugging."""
        if not respondents_list:
            return

        logger.debug(f"\n=== DEBUG: SAMPLE RESPONSE DATA ===")
        sample = respondents_list[0]
        logger.info(f"First respondent: {sample.respondent_id}")
        for resp in sample.responses:
            logger.info(f"  - {resp.question_name} ({resp.question_type}): {resp.value} (type: {type(resp.value)})")

        logger.debug(f"=== DEBUG END: Returning data for {len(respondents_list)} respondents ===")
