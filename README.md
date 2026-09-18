# Connect

Социальная сеть и мессенджер на Python, FastAPI, PostgreSQL и Redis.
Сейчас реализован backend регистрации, профилей, личных чатов и сообщений.

## Запуск на новых базах

Нужны Docker Compose и Python 3.12 для вспомогательных скриптов.

```powershell
python scripts/init_env.py
docker compose up -d --build --wait
```

Swagger UI:

- Auth: http://localhost:8000/docs
- Users: http://localhost:8001/docs
- Chats: http://localhost:8002/docs
- Messages: http://localhost:8003/docs

Если уже есть старые тома PostgreSQL, сначала прочитайте
[инструкцию переноса и настройки паролей](docs/DEVELOPMENT.md).
`init_env.py` создаёт секреты для новых баз; он не меняет пароли в старых томах.

## Сообщения

HTTP и WebSocket используют общую проверку доступа, сохранение и рассылку.
Redis доставляет события между экземплярами сервиса; история хранится в PostgreSQL.

WebSocket: `/ws/chats/{chat_id}`. В течение 5 секунд после подключения отправьте:

```json
{"type":"auth","token":"<access token>"}
```

После `{"type":"ready","chat_id":1}` отправляйте текстовые сообщения.
Токен не передаётся в URL. При его истечении соединение закрывается.
Для ручной проверки есть `websocket-test.html`: укажите адрес сервера, JWT и ID чата.

История: `GET /messages/chat/{chat_id}?limit=50&after_id=0` с Bearer-токеном.
После переподключения загрузите пропущенные сообщения через историю.

## Проверки

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r services/message-service/requirements.txt
.\.venv\Scripts\python.exe scripts/test_all.py
```

На Linux используйте `.venv/bin/python`. GitHub Actions запускает модульные
проверки, миграции на PostgreSQL и сквозной тест с двумя экземплярами message-service.
Команды для изолированного тестового стека — в [DEVELOPMENT.md](docs/DEVELOPMENT.md).

[Текущее состояние и ограничения](docs/PROJECT_STATUS.md).
