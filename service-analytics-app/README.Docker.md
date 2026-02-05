# Docker Setup для Service Analytics App
Этот документ описывает, как запустить приложение через Docker Compose.

## Требования

- Docker Desktop
- Минимум 2GB свободной оперативной памяти

## Быстрый старт

1. Перейдите в корневую директорию проекта:
```bash
cd service-analytics-app
```

2. Запустите все сервисы:
```bash
docker-compose up --build
```

3. Приложение будет доступно:
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - PostgreSQL: localhost:5432

## Команды

### Запуск в фоновом режиме
```bash
docker-compose up -d
```

### Остановка сервисов
```bash
docker-compose down
```

### Остановка с удалением volumes (удалит данные БД)
```bash
docker-compose down -v
```

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Пересборка образов
```bash
docker-compose build --no-cache
```

## Инициализация базы данных

После первого запуска контейнеров, вам может потребоваться инициализировать базу данных:

```bash
# Войти в контейнер backend
docker-compose exec backend bash

# Запустить скрипт загрузки данных
python src/load_data.py
```

## Структура сервисов

- **postgres**: База данных PostgreSQL на порту 5432
- **backend**: FastAPI приложение на порту 8000
- **frontend**: Vue.js приложение на порту 80 (nginx)

## Переменные окружения

Вы можете настроить переменные окружения в `docker-compose.yml`:

- `DATABASE_URL`: URL подключения к базе данных
- `CORS_ORIGINS`: Разрешенные источники для CORS (через запятую)
- `POSTGRES_USER`: Пользователь PostgreSQL
- `POSTGRES_PASSWORD`: Пароль PostgreSQL
- `POSTGRES_DB`: Имя базы данных

## Устранение проблем

### Порт уже занят
Если порт занят, измените маппинг портов в `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"
```

### Проблемы с подключением к БД
Убедитесь, что контейнер postgres запущен и здоров:
```bash
docker-compose ps
docker-compose logs postgres
```

### Пересборка после изменений в коде
```bash
docker-compose up --build
```

### Проблемы со сборкой (таймауты, сетевые ошибки)

Если сборка падает с ошибками сети или таймаутами:

1. **Используйте Docker BuildKit** (рекомендуется):
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
docker-compose up --build
```

2. **Соберите образы по отдельности** для экономии памяти:
```bash
# Сначала backend
docker-compose build backend

# Затем frontend
docker-compose build frontend

# И запустите все
docker-compose up
```

3. **Очистите кеш и пересоберите**:
```bash
docker-compose build --no-cache backend
docker-compose up
```

4. **Проверьте интернет-соединение** - установка системных пакетов требует стабильного соединения

5. **Используйте зеркала репозиториев** (если проблема с доступом к официальным репозиториям):
   - Для Debian: настройте `/etc/apt/sources.list` в Dockerfile
   - Для pip: используйте `--index-url` с альтернативным индексом
