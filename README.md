# Survey Analytics Application

Веб-приложение для работы с базой данных опросов и анализа ответов респондентов.

## Структура проекта

```
ORO_test/
├── input/                          # Входные данные
│   ├── responses.xlsx             # Ответы респондентов
│   └── xml/                       # XML файлы со структурой опросов
│       ├── QS0001.xml
│       └── ...
└── service-analytics-app/
    ├── backend/                   # FastAPI backend
    │   ├── src/
    │   │   ├── models/            # SQLAlchemy модели
    │   │   ├── routers/           # API роутеры
    │   │   ├── load_data.py       # Скрипт загрузки данных
    │   │   ├── main.py            # Точка входа FastAPI
    │   │   └── schemas.py         # Pydantic схемы
    │   ├── requirements.txt
    │   └── .env.example
    └── frontend/                   # Vue.js frontend
        ├── src/
        │   ├── api/               # API клиент
        │   ├── components/        # Vue компоненты
        │   ├── stores/            # Pinia stores
        │   ├── views/             # Страницы
        │   └── router/            # Vue Router
        ├── package.json
        └── vite.config.js
```

## Технологии

### Backend
- **FastAPI** - современный веб-фреймворк для Python
- **SQLAlchemy** - ORM для работы с PostgreSQL
- **PostgreSQL** - реляционная база данных
- **Pydantic** - валидация данных

### Frontend
- **Vue 3** - прогрессивный JavaScript фреймворк
- **Vuetify 3** - Material Design компоненты
- **Pinia** - state management
- **Vue Router** - маршрутизация
- **Axios** - HTTP клиент

## Установка и запуск

### Требования
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Запуск через Docker приоритетно
   # Смотреть в service-analytics-app\README.Docker.md

### Backend

1. Установите зависимости:
```bash
cd service-analytics-app/backend
pip install -r requirements.txt
```

2. Создайте базу данных PostgreSQL:
```sql
CREATE DATABASE survey_db;
```

3. Настройте переменные окружения (создайте `.env` файл на основе `.env.example`):
```bash
cp .env.example .env
# Отредактируйте .env с вашими настройками БД
```

4. Загрузите данные в базу:
```bash
python -m src.load_data
```

5. Запустите сервер:
```bash
uvicorn src.main:app --reload --port 8000
```

### Frontend

1. Установите зависимости:
```bash
cd service-analytics-app/frontend
npm install
```

2. Запустите dev сервер:
```bash
npm run dev
```

Приложение будет доступно по адресу `http://localhost:5173`

## Использование

### Основной функционал

1. **Настройка отображения ответов** (`/`)
   - Выберите опрос из выпадающего списка
   - Введите ID вопросов через запятую
   - Нажмите "Проверить заполнение" для валидации
   - После успешной валидации нажмите "Отобразить" для просмотра таблицы

2. **Просмотр всех ответов по опросу** (`/survey/<survey_id>`)
   - Отображает таблицу со всеми ответами по всем вопросам опроса
   - При наведении на ячейки с вопросами SINGLE/MULTIPLE показываются коды и текстовые метки

### API Endpoints

- `GET /api/surveys/` - получить список всех опросов
- `GET /api/surveys/{survey_id}/questions` - получить вопросы опроса
- `POST /api/surveys/validate-questions` - валидация вопросов
- `POST /api/surveys/responses` - получить ответы по выбранным вопросам
- `GET /api/surveys/{survey_id}/all-responses` - получить все ответы по опросу
- `GET /api/answer-options/question/{question_id}` - получить варианты ответов для вопроса

## Структура базы данных

### Таблицы

- **surveys** - опросы
- **questions** - вопросы опросов
- **respondents** - респонденты
- **answer_options** - варианты ответов для вопросов типа SINGLE/MULTIPLE
- **text_responses** - текстовые ответы
- **choice_responses** - ответы с выбором вариантов

### Типы вопросов

- **TEXT (1)** - текстовый ответ
- **SINGLE (2)** - один вариант из списка
- **MULTIPLE (3)** - несколько вариантов из списка

## Особенности реализации

1. **Архитектура**: Применены принципы ООП, разделение на слои (models, routers, schemas)
2. **Валидация**: Использованы Pydantic схемы для валидации запросов/ответов
3. **ORM**: SQLAlchemy для работы с БД, использование relationships для связей
4. **State Management**: Pinia для управления состоянием во frontend
5. **UI Components**: Готовые компоненты Vuetify для быстрой разработки

## Упрощения

- Порядок ответов в MULTIPLE вопросах может быть не полностью сохранен (используется сортировка по order)
- Пагинация не реализована (как указано в задании)
- Проблема ширины таблицы при большом количестве вопросов не решена (как указано в задании)

## Разработка

### Запуск в режиме разработки

Backend с автоперезагрузкой:
```bash
uvicorn src.main:app --reload
```

Frontend с hot-reload:
```bash
npm run dev
```

### Сборка для продакшена

Frontend:
```bash
npm run build
```

Backend:
```bash
# Используйте production WSGI сервер (например, gunicorn)
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

