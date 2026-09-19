# Развёртывание Connect на Linux-сервере

## Первый запуск

Нужны Docker Engine, Compose **2.24.4 или новее**, Git и Python 3.
Конфигурация рассчитана на один сервер. DNS A-запись домена должна указывать на
его публичный IP; AAAA добавляйте только при работающем IPv6. Откройте TCP 80/443
и UDP 443. Порт SSH оставьте доступным для администрирования.

```bash
git clone https://github.com/timurckaaslanov13/Connect.git
cd Connect
umask 077
python3 scripts/init_env.py
chmod 600 .env
```

В `.env` заполните `CONNECT_DOMAIN` (например `connect.example.com`, без `https://`
и пути) и `ACME_EMAIL` — адрес для сертификата. Остальные сгенерированные секреты
сохраните. Для существующих баз нужны их текущие пароли: генератор не меняет
пароли в PostgreSQL. `.env` не отправляйте в GitHub.

```bash
docker compose -p connect -f docker-compose.yml -f docker-compose.production.yml up -d --build --wait
docker compose -p connect -f docker-compose.yml -f docker-compose.production.yml ps
```

Откройте `https://ВАШ-ДОМЕН`. Caddy получает сертификат и обновляет его автоматически.
Снаружи опубликованы только 80/443; порты БД, Redis и API не публикуются.
Не запускайте на сервере один `docker-compose.yml` без production-файла.

Миграции выполняются при запуске сервисов. Если старая база содержит ники,
отличающиеся только регистром, миграция остановится: сначала разрешите конфликт
этих аккаунтов. Автоматического переименования пользователей нет.

## Звонки

HTTPS нужен для разрешений камеры/микрофона вне localhost. Для устойчивого
соединения между разными сетями нужен TURN-сервер. В `.env` задайте `TURN_URLS`
(через запятую) и `TURN_SECRET` от сервера с HMAC REST-авторизацией.
Без TURN прямые звонки могут работать в одной сети и не соединяться в другой.
TURN в этом комплекте не развёртывается. Внешний TURN потребует своих портов;
одного веб-прокси для передачи медиа недостаточно.

## Резервная копия перед обновлением

Для согласованной копии четырёх баз остановите запись на короткое время.
Базы и Redis остаются запущенными. Команда не удаляет тома.

```bash
docker compose -p connect -f docker-compose.yml -f docker-compose.production.yml stop web auth-service user-service chat-service message-service
python3 scripts/backup.py --project connect --output backups
docker compose -p connect -f docker-compose.yml -f docker-compose.production.yml up -d --wait
```

Скрипт создаёт четыре `.dump`, проверяет читаемость каталогов `pg_restore` и пишет
SHA-256 в manifest.json. Если он завершился ошибкой, копия неполная; не используйте
её для восстановления. Проверка каталога не заменяет пробное восстановление.
Отдельно сохраните `.env` в защищённое хранилище. Копии содержат пользовательские
данные: храните их зашифрованными вне сервера, с ограниченным доступом.

Для пробного восстановления создайте **отдельный** Compose-проект и новые тома,
восстановите четыре дампа через `pg_restore --no-owner --no-acl` в пустые базы,
затем запустите API и проверьте вход, профили, чаты и историю. Не восстанавливайте
дампы поверх рабочих баз и не используйте `down --volumes` на рабочем проекте.

## Обновление

После резервной копии:

```bash
git pull --ff-only
docker compose -p connect -f docker-compose.yml -f docker-compose.production.yml up -d --build --wait
```

При неудаче смотрите журналы, не удаляйте тома:

```bash
docker compose -p connect -f docker-compose.yml -f docker-compose.production.yml logs --tail 100 gateway web auth-service user-service chat-service message-service
```

Старую версию кода нельзя считать безопасным откатом после изменения схемы БД:
сначала проверьте совместимость миграций или восстановление копии в отдельном проекте.

## Границы текущего выпуска

Это веб-версия ядра мессенджера. Подтверждение email и восстановление доступа
отложены по решению владельца проекта. Пока нет вложений, групп, каналов и push.
Перед приглашением пользователей проверьте звонки на реальных устройствах через
разные сети. Сертификат публичного домена и доставка медиа проверяются уже на сервере.

Источники настройки: [Caddy Automatic HTTPS](https://caddyserver.com/docs/automatic-https),
[Docker Compose merge](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/).
