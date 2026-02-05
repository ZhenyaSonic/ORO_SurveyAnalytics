# Быстрый старт

## Шаг 1: Настройка базы данных

1. Установите PostgreSQL и создайте базу данных:
```sql
CREATE DATABASE survey_db;
```

2. Настройте переменные окружения (создайте файл `service-analytics-app/backend/.env`):
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/survey_db
```

## Шаг 2: Backend

1. Перейдите в директорию backend:
```bash
cd service-analytics-app/backend
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

3. Загрузите данные в базу:
```bash
python -m src.load_data
```

4. Запустите сервер:
```bash
python run.py
# или
uvicorn src.main:app --reload --port 8000
```

Backend будет доступен по адресу: http://localhost:8000

## Шаг 3: Frontend

1. Откройте новый терминал и перейдите в директорию frontend:
```bash
cd service-analytics-app/frontend
```

2. Установите зависимости:
```bash
npm install
```

3. Запустите dev сервер:
```bash
npm run dev
```

Frontend будет доступен по адресу: http://localhost:5173

## Использование

1. Откройте браузер и перейдите на http://localhost:5173
2. Выберите опрос из выпадающего списка
3. Введите ID вопросов через запятую (например: `b7895b40-cdce-4080-9c48-d767e72640e4, f60ccc57-f829-41c9-bf73-f3cf58915261`)
4. Нажмите "Проверить заполнение"
5. После успешной валидации нажмите "Отобразить" для просмотра таблицы

Для просмотра всех ответов по опросу перейдите по адресу: http://localhost:5173/survey/QS0001 (замените QS0001 на нужный ID опроса)

