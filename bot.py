import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import jdatetime
from dotenv import load_dotenv
from openpyxl import Workbook
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from database import AttendanceDB

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "attendance.db"
TEHRAN = ZoneInfo("Asia/Tehran")

TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Copy .env.example to .env and set your Telegram bot token."
    )

db = AttendanceDB(DB_PATH)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("attendance-bot")

CHECK_IN = "✅ ورود"
CHECK_OUT = "🚪 خروج"
TODAY_REPORT = "📋 گزارش امروز"
MONTH_REPORT = "📅 گزارش ماه"
MY_EXCEL = "📤 اکسل من"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [CHECK_IN, CHECK_OUT],
        [TODAY_REPORT, MONTH_REPORT],
        [MY_EXCEL],
    ],
    resize_keyboard=True,
)


def now_tehran() -> datetime:
    return datetime.now(TEHRAN)


def jalali_text(dt: datetime) -> str:
    jdt = jdatetime.datetime.fromgregorian(datetime=dt)
    return jdt.strftime("%Y/%m/%d - %H:%M")


def display_name(update: Update) -> str:
    user = update.effective_user
    if not user:
        return "Unknown"
    name = " ".join(x for x in [user.first_name, user.last_name] if x).strip()
    return name or user.username or str(user.id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    db.upsert_user(
        telegram_id=update.effective_user.id,
        name=display_name(update),
        username=update.effective_user.username,
    )

    await update.message.reply_text(
        "سلام 👋\n"
        "این بات برای ثبت ورود و خروج و گرفتن گزارش حضور طراحی شده.",
        reply_markup=MAIN_KEYBOARD,
    )


async def handle_check_in(update: Update) -> None:
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    db.upsert_user(user_id, display_name(update), update.effective_user.username)

    if db.has_open_session(user_id):
        await update.message.reply_text("⚠️ یک ورود باز داری؛ اول باید خروج ثبت کنی.")
        return

    ts = now_tehran()
    db.check_in(user_id, ts)
    await update.message.reply_text(f"✅ ورود ثبت شد\n{jalali_text(ts)}")


async def handle_check_out(update: Update) -> None:
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id

    if not db.has_open_session(user_id):
        await update.message.reply_text("⚠️ ورود بازی پیدا نشد؛ اول ورود را ثبت کن.")
        return

    ts = now_tehran()
    session = db.check_out(user_id, ts)

    duration = ""
    if session and session["check_in"]:
        started = datetime.fromisoformat(session["check_in"])
        total_minutes = int((ts - started).total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        duration = f"\n⏱ مدت حضور: {hours} ساعت و {minutes} دقیقه"

    await update.message.reply_text(
        f"🚪 خروج ثبت شد\n{jalali_text(ts)}{duration}"
    )


def format_sessions(sessions: list[dict]) -> str:
    if not sessions:
        return "رکوردی پیدا نشد."

    lines = []
    total_minutes = 0

    for i, row in enumerate(sessions, start=1):
        check_in = datetime.fromisoformat(row["check_in"])
        check_out = (
            datetime.fromisoformat(row["check_out"])
            if row["check_out"]
            else None
        )

        in_text = jdatetime.datetime.fromgregorian(
            datetime=check_in
        ).strftime("%Y/%m/%d %H:%M")

        if check_out:
            out_text = jdatetime.datetime.fromgregorian(
                datetime=check_out
            ).strftime("%H:%M")
            mins = int((check_out - check_in).total_seconds() // 60)
            total_minutes += max(mins, 0)
            hours, minutes = divmod(max(mins, 0), 60)
            duration_text = f"{hours:02d}:{minutes:02d}"
        else:
            out_text = "باز"
            duration_text = "-"

        lines.append(
            f"{i}) {in_text} → {out_text} | ⏱ {duration_text}"
        )

    if total_minutes:
        hours, minutes = divmod(total_minutes, 60)
        lines.append(f"\nمجموع: {hours} ساعت و {minutes} دقیقه")

    return "\n".join(lines)


async def today_report(update: Update) -> None:
    if not update.effective_user or not update.message:
        return

    sessions = db.get_today_sessions(update.effective_user.id, now_tehran())
    await update.message.reply_text(
        "📋 گزارش امروز\n\n" + format_sessions(sessions)
    )


async def month_report(update: Update) -> None:
    if not update.effective_user or not update.message:
        return

    sessions = db.get_current_jalali_month_sessions(
        update.effective_user.id,
        now_tehran(),
    )
    await update.message.reply_text(
        "📅 گزارش ماه جاری\n\n" + format_sessions(sessions)
    )


def make_excel(rows: list[dict], output_path: Path, title: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    ws.append(
        [
            "Telegram ID",
            "Name",
            "Username",
            "Check-in (Jalali)",
            "Check-out (Jalali)",
            "Duration (minutes)",
        ]
    )

    for row in rows:
        check_in = datetime.fromisoformat(row["check_in"])
        check_out = (
            datetime.fromisoformat(row["check_out"])
            if row["check_out"]
            else None
        )

        check_in_j = jdatetime.datetime.fromgregorian(
            datetime=check_in
        ).strftime("%Y/%m/%d %H:%M")

        if check_out:
            check_out_j = jdatetime.datetime.fromgregorian(
                datetime=check_out
            ).strftime("%Y/%m/%d %H:%M")
            duration = int((check_out - check_in).total_seconds() // 60)
        else:
            check_out_j = ""
            duration = ""

        ws.append(
            [
                row["telegram_id"],
                row["name"],
                row["username"] or "",
                check_in_j,
                check_out_j,
                duration,
            ]
        )

    ws.freeze_panes = "A2"
    wb.save(output_path)


async def export_my_excel(update: Update) -> None:
    if not update.effective_user or not update.message:
        return

    rows = db.get_current_jalali_month_sessions_with_user(
        update.effective_user.id,
        now_tehran(),
    )

    if not rows:
        await update.message.reply_text("برای ماه جاری رکوردی نداری.")
        return

    output_path = BASE_DIR / f"attendance_{update.effective_user.id}.xlsx"
    try:
        make_excel(rows, output_path, "My Attendance")
        with output_path.open("rb") as f:
            await update.message.reply_document(
                document=f,
                filename="my_attendance.xlsx",
                caption="📤 خروجی ماه جاری",
            )
    finally:
        output_path.unlink(missing_ok=True)


async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ این دستور فقط برای ادمین است.")
        return

    rows = db.get_all_current_jalali_month_sessions(now_tehran())
    if not rows:
        await update.message.reply_text("برای ماه جاری رکوردی وجود ندارد.")
        return

    output_path = BASE_DIR / "attendance_admin.xlsx"
    try:
        make_excel(rows, output_path, "All Attendance")
        with output_path.open("rb") as f:
            await update.message.reply_document(
                document=f,
                filename="attendance_all_users.xlsx",
                caption="📊 خروجی ماه جاری همه کاربران",
            )
    finally:
        output_path.unlink(missing_ok=True)


async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    text = (update.message.text or "").strip()

    if text == CHECK_IN:
        await handle_check_in(update)
    elif text == CHECK_OUT:
        await handle_check_out(update)
    elif text == TODAY_REPORT:
        await today_report(update)
    elif text == MONTH_REPORT:
        await month_report(update)
    elif text == MY_EXCEL:
        await export_my_excel(update)
    else:
        await update.message.reply_text(
            "از دکمه‌های منو استفاده کن 👇",
            reply_markup=MAIN_KEYBOARD,
        )


def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin_export", admin_export))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_router)
    )

    logger.info("Starting attendance bot...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
