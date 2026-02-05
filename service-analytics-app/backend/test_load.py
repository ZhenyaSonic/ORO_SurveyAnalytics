import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
from src.models import SessionLocal

# Проверяем чтение Excel
excel_path = Path('/app/input/responses.xlsx')
df = pd.read_excel(excel_path)

print("Тестируем первые 10 строк:")
for i in range(min(10, len(df))):
    row = df.iloc[i]
    text = str(row.get("text", "")).strip()
    response = str(row.get("response", "")).strip()
    
    print(f"\nСтрока {i}:")
    print(f"  survey: {row['survey']}")
    print(f"  type: {row['type']}")
    print(f"  text: '{text}' (len: {len(text)}, bool: {bool(text)})")
    print(f"  response: '{response}' (len: {len(response)}, bool: {bool(response)})")
    
    # Проверяем условия из вашего кода
    if row['type'] == 1:
        print(f"  Условие 'if text:': {bool(text)}")
    elif row['type'] in [2, 3]:
        print(f"  Условие 'if response_id:': {bool(response)}")

# Проверяем базу данных
print("\n\nПроверяем базу данных:")
db = SessionLocal()
from src.models import Respondent, TextResponse, ChoiceResponse

print(f"Респонденты в БД: {db.query(Respondent).count()}")
print(f"TextResponse в БД: {db.query(TextResponse).count()}")
print(f"ChoiceResponse в БД: {db.query(ChoiceResponse).count()}")

db.close()