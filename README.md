# Telegram Attendance Bot 🤖

A simple Telegram attendance bot built with Python.

It records check-in/check-out sessions, prevents duplicate open sessions, supports Jalali dates, generates daily/monthly reports, and exports attendance data to Excel.

## Features

- ✅ Check-in and check-out
- ✅ Prevent duplicate open check-ins
- ✅ Prevent check-out without an active session
- ✅ Tehran timezone
- ✅ Jalali date display
- ✅ Daily attendance report
- ✅ Current Jalali month report
- ✅ Personal Excel export
- ✅ Admin Excel export for all users
- ✅ SQLite storage
- ✅ Environment-variable based secrets

## Tech Stack

- Python
- python-telegram-bot
- SQLite
- jdatetime
- openpyxl
- python-dotenv

## Project Structure

```text
telegram-attendance-bot/
├── bot.py
├── database.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/telegram-attendance-bot.git
cd telegram-attendance-bot
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and set your own values:

```env
BOT_TOKEN=your_real_bot_token
ADMIN_IDS=123456789
```

> Never commit your real `.env` file or bot token.

### 5. Run

```bash
python bot.py
```

## Telegram Commands

- `/start` — show the main menu
- `/admin_export` — export the current Jalali month for all users (admin only)

## Security

Secrets are loaded from environment variables. The local SQLite database and generated Excel files are excluded from Git by `.gitignore`.

## Roadmap

- Manual date editing
- Monthly attendance summary by hours
- Admin user management
- Better Excel formatting
- Docker deployment
- PostgreSQL support
- Automated tests

## License

MIT
