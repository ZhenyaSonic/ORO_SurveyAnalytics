"""
Script to load survey data from XML files and Excel responses into PostgreSQL.

Can be run both as:
- `python -m src.load_data` (recommended inside Docker)
- `python src/load_data.py` (from project root)
"""
import os
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
from src.logger import logger

try:
    from .models import (
        Base,
        engine,
        SessionLocal,
        Survey,
        Question,
        QuestionType,
        Respondent,
        AnswerOption,
        TextResponse,
        ChoiceResponse,
    )
except ImportError:
    from src.models import (
        Base,
        engine,
        SessionLocal,
        Survey,
        Question,
        QuestionType,
        Respondent,
        AnswerOption,
        TextResponse,
        ChoiceResponse,
    )


def parse_xml_survey(xml_path: Path, survey_id: str, db: Session) -> None:
    """Parse XML file and load survey structure into database."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        survey = Survey(id=survey_id)
        db.add(survey)
        db.flush()

    questions_elem = root.find(".//questions")
    if questions_elem is not None:
        for question_elem in questions_elem.findall("question"):
            question_id = question_elem.get("id")
            question_type = int(question_elem.get("type"))
            name_elem = question_elem.find("name")
            text_elem = question_elem.find("text")

            name = name_elem.text if name_elem is not None else ""
            text = text_elem.text if text_elem is not None else ""

            type_map = {1: QuestionType.TEXT, 2: QuestionType.SINGLE, 3: QuestionType.MULTIPLE}
            question_type_enum = type_map.get(question_type, QuestionType.TEXT)

            question = db.query(Question).filter(Question.id == question_id).first()
            if not question:
                question = Question(
                    id=question_id,
                    survey_id=survey_id,
                    name=name,
                    text=text,
                    type=question_type_enum
                )
                db.add(question)
            else:
                question.name = name
                question.text = text
                question.type = question_type_enum

            db.flush()

            if question_type in [2, 3]:
                categories_elem = root.find(f".//categories[@id='{question_id}']")
                if categories_elem is not None:
                    for category_elem in categories_elem.findall("category"):
                        option_id = category_elem.get("id")
                        code = int(category_elem.get("code"))
                        label = category_elem.text if category_elem.text else ""

                        answer_option = db.query(AnswerOption).filter(
                            AnswerOption.id == option_id
                        ).first()
                        if not answer_option:
                            answer_option = AnswerOption(
                                id=option_id,
                                question_id=question_id,
                                code=code,
                                label=label
                            )
                            db.add(answer_option)
                        else:
                            answer_option.code = code
                            answer_option.label = label


def load_responses_from_excel(excel_path: Path, db: Session) -> None:
    """Load responses from Excel file into database."""
    logger.info(f"Loading Excel file from: {excel_path}")

    df = pd.read_excel(excel_path)
    df = df.replace('nan', pd.NA)

    logger.info(f"Excel loaded successfully! Rows: {len(df)}")

    text_responses_count = 0
    choice_responses_count = 0
    respondents_count = 0
    respondents_cache = {}

    for idx, row in df.iterrows():
        survey_id = str(row["survey"])
        respondent_id = str(row["respondent"])
        question_id = str(row["question"])
        question_type = int(row["type"])

        if idx % 10000 == 0:
            logger.info(f"Processing row {idx}/{len(df)}...")

        if respondent_id not in respondents_cache:

            respondent = db.query(Respondent).filter_by(id=respondent_id).first()
            if not respondent:
                respondent = Respondent(id=respondent_id)
                db.add(respondent)
                respondents_count += 1
            respondents_cache[respondent_id] = respondent

        if question_type == 1:
            if pd.notna(row.get("text")):
                text = str(row["text"]).strip()
                if text.lower() != 'nan' and text:
                    existing = db.query(TextResponse).filter_by(
                        respondent_id=respondent_id,
                        question_id=question_id,
                        survey_id=survey_id
                    ).first()

                    if not existing:
                        text_response = TextResponse(
                            respondent_id=respondent_id,
                            question_id=question_id,
                            survey_id=survey_id,
                            text=text
                        )
                        db.add(text_response)
                        text_responses_count += 1

        elif question_type in [2, 3]:
            if pd.notna(row.get("response")):
                response_id = str(row["response"]).strip()
                order = int(row["order"]) if pd.notna(row.get("order")) else 1

                if response_id.lower() != 'nan' and response_id:
                    existing = db.query(ChoiceResponse).filter_by(
                        respondent_id=respondent_id,
                        question_id=question_id,
                        survey_id=survey_id,
                        answer_option_id=response_id
                    ).first()

                    if not existing:
                        choice_response = ChoiceResponse(
                            respondent_id=respondent_id,
                            question_id=question_id,
                            survey_id=survey_id,
                            answer_option_id=response_id,
                            response_order=order
                        )
                        db.add(choice_response)
                        choice_responses_count += 1

        if idx > 0 and idx % 5000 == 0:
            try:
                db.commit()
                logger.info(f"Committed {idx} rows...")
            except Exception as e:
                db.rollback()
                logger.info(f"Error at row {idx}, rolling back: {e}")
                continue

    try:
        db.commit()
    except Exception as e:
        logger.info(f"Final commit error: {e}")
        db.rollback()
        raise

    logger.info(f"\n=== Loading Summary ===")
    logger.info(f"Total rows in Excel: {len(df)}")
    logger.info(f"Unique respondents created: {respondents_count}")
    logger.info(f"Text responses added: {text_responses_count}")
    logger.info(f"Choice responses added: {choice_responses_count}")
    logger.info(f"Total responses added: {text_responses_count + choice_responses_count}")


def load_all_data(xml_dir: Path, excel_path: Path, db: Session) -> None:
    """Load all survey data from XML files and Excel responses."""
    logger.info("Loading surveys from XML files...")

    xml_files = sorted(xml_dir.glob("*.xml"))
    for xml_file in xml_files:
        survey_id = xml_file.stem
        logger.info(f"Loading survey {survey_id} from {xml_file.name}...")
        parse_xml_survey(xml_file, survey_id, db)
        db.commit()

    logger.info("Loading responses from Excel file...")
    load_responses_from_excel(excel_path, db)
    db.commit()
    logger.info("Data loading completed!")


def main():
    """Main function to create database and load data."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    base_dir = Path(os.getenv("INPUT_BASE_DIR", Path(__file__).resolve().parent.parent))
    xml_dir = base_dir / "input" / "xml"
    excel_path = base_dir / "input" / "responses.xlsx"

    db = SessionLocal()

    try:
        load_all_data(xml_dir, excel_path, db)
    except Exception as e:
        logger.info(f"Error loading data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
