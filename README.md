# 🧠 Neuro Aggregator Bot

Telegram-бот «Агрегатор бесплатных нейросетей» — один бот для генерации картинок,
текста, озвучки, распознавания речи и суммаризации YouTube. Монетизация через
**Telegram Stars** (встроенные платежи).

## ✨ Возможности

| Функция | Сервис | Fallback |
|---|---|---|
| 📝 Генерация текста | Groq (llama-3.3-70b-versatile) | Google Gemini 2.0 Flash |
| 🖼 Генерация картинок | Pollinations.ai | HuggingFace FLUX.1-schnell |
| 🔊 Озвучка (TTS) | edge-tts (бесплатно, без ключа) | — |
| 🎤 Распознавание (STT) | Groq Whisper large-v3-turbo | — |
| 🎬 Суммаризация YouTube | youtube-transcript-api + Groq | — |
| 💎 Premium | Telegram Stars (100 ⭐ / 30 дней) | — |

**Лимиты:** 5 бесплатных запросов в сутки (сбрасываются каждые 24 ч). Premium — безлимит.

---

## 🚀 Быстрый старт

### 1. Получите ключи

- **BOT_TOKEN** — у [@BotFather](https://t.me/BotFather): `/newbot` → токен.
- **ADMIN_IDS** — свой Telegram ID (узнать: [@userinfobot](https://t.me/userinfobot)).
- **GROQ_API_KEY** — https://console.groq.com/keys (бесплатно).
- **GEMINI_API_KEY** — https://aistudio.google.com/app/apikey (бесплатно).
- **HUGGINGFACE_API_KEY** — https://huggingface.co/settings/tokens (роль: read).

### 2. Клонируйте и настройте

```bash
git clone <your-repo> neuro_aggregator
cd neuro_aggregator
cp .env.example .env
# откройте .env и вставьте свои ключи
```

### 3. Запуск через Docker (рекомендуется)

```bash
docker compose up -d --build
docker compose logs -f
```

### 4. Запуск локально (Python 3.11+)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 💎 Как включить Telegram Stars

1. В [@BotFather](https://t.me/BotFather) → `/mybots` → ваш бот → **Payments** → подключить платежи.
2. Для Stars **provider_token не нужен** — оставьте пустым (в коде уже так).
3. Валюта — `XTR` (задана в `payments.py`).

---

## 🌍 Деплой на Railway / Render (бесплатно)

### Railway
1. Форкните репозиторий на GitHub.
2. [railway.app](https://railway.app) → New Project → Deploy from GitHub → выберите репо.
3. Variables → добавьте все переменные из `.env`.
4. Railway сам соберёт Dockerfile и запустит.

### Render
1. [render.com](https://render.com) → New → **Background Worker** (не Web Service!).
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python main.py`
4. Environment → добавьте переменные из `.env`.

> ⚠️ На бесплатных тарифах SQLite-файл может теряться при рестарте. Для продакшена
> задайте `DATABASE_URL` (Railway/Render дают бесплатный PostgreSQL).
> Формат: `postgresql+asyncpg://user:pass@host:5432/dbname`

---

## 🛠 Админ-команды

| Команда | Описание |
|---|---|
| `/stats` | Статистика: юзеры, запросы, платежи |
| `/broadcast <текст>` | Рассылка всем пользователям |
| `/give <user_id> <days>` | Выдать Premium вручную |
| `/reset_user <user_id>` | Сбросить дневные лимиты |

---

## 📁 Структура

```
neuro_aggregator/
├── main.py                 # точка входа
├── config.py               # pydantic-settings
├── database/               # SQLAlchemy 2.0 async
├── handlers/               # роутеры aiogram
├── services/               # клиенты внешних API
├── middlewares/            # throttling + limits
├── keyboards/              # reply/inline клавиатуры
├── states/                 # FSM
├── utils/                  # тексты
├── Dockerfile
└── docker-compose.yml
```

---

## 🧪 Полезное

- Логи: `logs/bot.log`
- Локальная БД: `bot.db` (SQLite)
- Проверить платежи: логи `Payment success: ...`

---

## 📜 Лицензия

MIT — используйте свободно.