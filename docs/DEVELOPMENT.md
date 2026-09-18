# Запуск и миграции

Для нового проекта: `docker compose up -d --build --wait`. Каждый сервис ждёт
готовности своей БД и выполняет `alembic upgrade head` перед запуском API.
Данные сохраняются в именованных томах. Порты API по умолчанию 8000–8003,
PostgreSQL 5432–5435, доступны только на localhost. Их можно изменить через
AUTH_PORT, USER_PORT, CHAT_PORT, MESSAGE_PORT и соответствующие *_DB_PORT.

## Уже существующие базы

Начальные миграции предназначены для пустых баз. Если таблицы уже созданы
вручную, не удаляйте тома и не запускайте `downgrade base`: это удаляет таблицы.
Сначала сделайте резервную копию и сравните схему с начальной миграцией.
Только для совпадающей схемы можно отметить исходную версию:

```powershell
docker compose run --rm auth-service alembic stamp 0001
docker compose run --rm user-service alembic stamp 0001
docker compose run --rm chat-service alembic stamp 0001
docker compose run --rm message-service alembic stamp 0001
```

После этого `alembic upgrade head` применит последующие миграции. Если схема
отличается, нужна отдельная миграция переноса; stamp сам не исправляет таблицы.

## Изолированные проверки

Для тестов используйте отдельное имя Compose-проекта (`-p connect-check`) и
другие порты. Не используйте существующие тома проекта для тестов отката.
В тестовой БД проверяются upgrade → check → downgrade base → upgrade → check.
`alembic check` сравнивает актуальную схему с моделями.
