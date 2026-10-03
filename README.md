# Telegram Attendance Bot 🤖

A simple Telegram attendance bot built with Python for recording and managing attendance.

It supports check-in/check-out sessions, Jalali dates, daily and monthly reports, Excel export, SQLite storage, and basic admin functionality.

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
├── LICENSE
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/mohammadamiryan/telegram-attendance-bot.git
cd telegram-attendance-bot
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux

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

> Never commit your real `.env` file, Telegram bot token, passwords, or private credentials.

### 5. Run the bot

```bash
python bot.py
```

## Telegram Commands

- `/start` — show the main menu
- `/admin_export` — export attendance data for the current Jalali month for all users (admin only)

## Security

- Secrets are loaded from environment variables.
- `.env` is excluded from version control.
- The local SQLite database is excluded from version control.
- Generated Excel files are excluded from version control.

## Roadmap

Planned improvements include:

- Manual date editing
- Better monthly attendance summaries
- Admin user management
- Improved Excel formatting
- Automated tests
- Docker deployment
- PostgreSQL support
- More advanced reporting

## About This Project

This project was built as a practical Python project focused on automation, data storage, reporting, and Telegram bot development.

It is part of my ongoing journey in Python, software development, and data-driven healthcare technology.

## License

This project is licensed under the MIT License.
