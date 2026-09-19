# Connect

Социальная сеть и мессенджер на Python, FastAPI, PostgreSQL и Redis.
Реализованы адаптивный веб-интерфейс, регистрация, профили, поиск людей, заявки в друзья, личные чаты и аудио-/видеозвонки.

## Запуск на сервере

[Инструкция для Linux-сервера: HTTPS, обновление и резервные копии](docs/DEPLOYMENT.md).
Поиск друзей работает по уникальному нику, без учёта регистра; имена могут повторяться.
Подтверждение email и восстановление доступа пока отложены.

## Запуск на новых базах

Нужны Docker Compose и Python 3.12 для вспомогательных скриптов.

```powershell
python scripts/init_env.py
docker compose up -d --build --wait
```

Веб-приложение: http://localhost:8080 (изолированный стенд: http://localhost:18080).

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


## Интерфейс и звонки

`frontend` — React + TypeScript. Production-сборка обслуживается Nginx; API и
WebSocket доступны через тот же адрес. Для разработки: `cd frontend`,
`pnpm install --frozen-lockfile`, `pnpm dev` (прокси на стенд 18080).

Сообщения приходят через `/ws/events`; при возвращении в окно и каждые 5 секунд
в видимой вкладке история сверяется с сервером. Heartbeat поддерживает соединение.
Доступ к камере и микрофону запрашивается при начале или принятии звонка.

Для звонков за пределами localhost необходим HTTPS. Для сетей, где прямое
WebRTC-соединение невозможно, задайте `TURN_URLS` и `TURN_SECRET` от своего TURN
сервера с поддержкой временных HMAC-учётных данных. Один STUN не гарантирует
соединение между любыми сетями. Записи звука/видео сервер не хранит.

Браузерные тесты: `cd frontend`, `pnpm exec playwright test` при работающем стенде.
Они используют тестовую камеру/микрофон Chromium; физические устройства,
мобильные сети и приложения iOS/Android требуют отдельной проверки.
