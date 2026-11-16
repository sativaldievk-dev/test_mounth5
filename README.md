# Blog REST API

REST API для публикаций и комментариев на Django REST Framework. Проект
проверен на Python 3.13 и Django 5.2. В локальном режиме используется SQLite;
настройки подключения к PostgreSQL задаются переменными окружения.

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

Сгенерируйте секретный ключ и вставьте результат вместо пустого
`DJANGO_SECRET_KEY` в `.env`:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(64))'
```

Затем создайте таблицы, при необходимости создайте администратора и запустите
сервер:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API

| Метод | Путь | Назначение |
| --- | --- | --- |
| GET, POST | `/api/v1/posts/` | Список постов и создание поста |
| GET, PUT, PATCH, DELETE | `/api/v1/posts/{id}/` | Просмотр и управление своим постом |
| GET, POST | `/api/v1/posts/{id}/comments/` | Одобренные комментарии и создание комментария |
| GET, PUT, PATCH, DELETE | `/api/v1/comments/{id}/` | Просмотр и управление своим комментарием |
| POST | `/api/v1/token/` | Получить пару JWT-токенов |
| POST | `/api/v1/token/refresh/` | Обновить access-токен |

Передавайте access-токен в заголовке `Authorization: Bearer <access-token>`.
Новые посты и комментарии создаются неопубликованными и неодобренными
соответственно. Автор может опубликовать свой пост через `PATCH`, а модератор
одобряет комментарии в Django Admin (`/admin/`). Поля автора, связи и статуса
одобрения нельзя подменить через API.

Список постов разбит на страницы по 10 записей. Размер можно передать через
`?page_size=5`; максимальный размер страницы — 100.

## Документация

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

Чтобы проверять закрытые операции в Swagger, нажмите **Authorize** и передайте
`Bearer <access-token>`.

## PostgreSQL

Установите и запустите PostgreSQL, задайте в `.env` `DB_ENGINE=postgresql`,
`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` и
`POSTGRES_PORT`. Драйвер Psycopg 3 уже включён в `requirements.txt`. Пароли и
секретный ключ храните только в локальном `.env` или переменных окружения.

## Проверки

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
git diff --check
```

Подробное описание моделей, прав, API, тестов и вопросов для защиты находится в
[отчёте по проекту](PROJECT_REPORT_RU.md).
