import pandas as pd
from pathlib import Path

def debug_excel_loading():
    excel_path = Path('/app/input/responses.xlsx')
    df = pd.read_excel(excel_path)
    
    print("="*60)
    print("🔍 ДЕБАГГИНГ ЗАГРУЗКИ EXCEL")
    print("="*60)
    
    print(f"\n📊 Всего строк: {len(df)}")
    print(f"Колонки: {df.columns.tolist()}")
    
    # Проверяем каждое условие загрузки
    counters = {
        'total_rows': len(df),
        'type_1': 0,
        'type_2_3': 0,
        'type_1_with_text': 0,
        'type_2_3_with_response': 0,
        'text_not_empty': 0,
        'response_not_none': 0
    }
    
    for idx, row in df.iterrows():
        question_type = row['type']
        
        if question_type == 1:
            counters['type_1'] += 1
            text = str(row['text']) if pd.notna(row.get('text')) else ""
            if text:
                counters['type_1_with_text'] += 1
            if text and text.strip():  # не пустая строка
                counters['text_not_empty'] += 1
                
        elif question_type in [2, 3]:
            counters['type_2_3'] += 1
            response_id = str(row['response']) if pd.notna(row.get('response')) else None
            if response_id:
                counters['type_2_3_with_response'] += 1
            if response_id and response_id.strip():  # не пустая строка
                counters['response_not_none'] += 1
    
    print(f"\n📈 РАСПРЕДЕЛЕНИЕ:")
    print(f"   type=1 (текстовые): {counters['type_1']}")
    print(f"   type=2,3 (выборные): {counters['type_2_3']}")
    
    print(f"\n✅ УСЛОВИЯ ЗАГРУЗКИ:")
    print(f"   type=1 с текстом: {counters['type_1_with_text']}")
    print(f"   type=1 с НЕпустым текстом: {counters['text_not_empty']}")
    print(f"   type=2,3 с response: {counters['type_2_3_with_response']}")
    print(f"   type=2,3 с НЕпустым response: {counters['response_not_none']}")
    
    # Проверяем несколько проблемных строк
    print(f"\n🔍 ПРОБЛЕМНЫЕ СТРОКИ (первые 5):")
    
    # Строки type=1 без текста
    type1_no_text = df[(df['type'] == 1) & (df['text'].isna())].head(5)
    if not type1_no_text.empty:
        print("\n  type=1 без текста:")
        for _, row in type1_no_text.iterrows():
            print(f"    Строка: survey={row['survey']}, respondent={row['respondent']}, question={row['question']}")
    
    # Строки type=2,3 без response
    type23_no_response = df[df['type'].isin([2,3]) & df['response'].isna()].head(5)
    if not type23_no_response.empty:
        print("\n  type=2,3 без response:")
        for _, row in type23_no_response.iterrows():
            print(f"    Строка: survey={row['survey']}, respondent={row['respondent']}, question={row['question']}")
    
    # Примеры корректных строк
    print(f"\n📋 ПРИМЕРЫ КОРРЕКТНЫХ СТРОК:")
    
    # type=1 с текстом
    type1_with_text = df[(df['type'] == 1) & (df['text'].notna())].head(3)
    if not type1_with_text.empty:
        print("\n  type=1 с текстом:")
        for _, row in type1_with_text.iterrows():
            print(f"    survey={row['survey']}, text='{row['text'][:30]}...'")
    
    # type=2,3 с response
    type23_with_response = df[df['type'].isin([2,3]) & df['response'].notna()].head(3)
    if not type23_with_response.empty:
        print("\n  type=2,3 с response:")
        for _, row in type23_with_response.iterrows():
            print(f"    survey={row['survey']}, response={row['response']}")

if __name__ == "__main__":
    debug_excel_loading()