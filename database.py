import sqlite3
from datetime import datetime, time, timedelta
from pathlib import Path

import jdatetime


class AttendanceDB:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._init_db()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    username TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    check_in TEXT NOT NULL,
                    check_out TEXT,
                    FOREIGN KEY (telegram_id)
                        REFERENCES users(telegram_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_user_checkin
                ON sessions(telegram_id, check_in);
                """
            )

    def upsert_user(self, telegram_id: int, name: str, username: str | None):
        now = datetime.now().astimezone().isoformat()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO users(telegram_id, name, username, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    name = excluded.name,
                    username = excluded.username,
                    updated_at = excluded.updated_at
                """,
                (telegram_id, name, username, now),
            )

    def has_open_session(self, telegram_id: int) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM sessions
                WHERE telegram_id = ? AND check_out IS NULL
                LIMIT 1
                """,
                (telegram_id,),
            ).fetchone()
            return row is not None

    def check_in(self, telegram_id: int, ts: datetime):
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions(telegram_id, check_in, check_out)
                VALUES (?, ?, NULL)
                """,
                (telegram_id, ts.isoformat()),
            )

    def check_out(self, telegram_id: int, ts: datetime) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, check_in
                FROM sessions
                WHERE telegram_id = ? AND check_out IS NULL
                ORDER BY check_in DESC
                LIMIT 1
                """,
                (telegram_id,),
            ).fetchone()

            if row is None:
                return None

            conn.execute(
                "UPDATE sessions SET check_out = ? WHERE id = ?",
                (ts.isoformat(), row["id"]),
            )
            return dict(row)

    def get_today_sessions(self, telegram_id: int, now: datetime) -> list[dict]:
        start = datetime.combine(now.date(), time.min, tzinfo=now.tzinfo)
        end = start + timedelta(days=1)
        return self._get_user_sessions_between(telegram_id, start, end)

    def _jalali_month_bounds(self, now: datetime):
        j_now = jdatetime.datetime.fromgregorian(datetime=now)
        start_j = jdatetime.datetime(j_now.year, j_now.month, 1, 0, 0, 0)

        if j_now.month == 12:
            next_j = jdatetime.datetime(j_now.year + 1, 1, 1, 0, 0, 0)
        else:
            next_j = jdatetime.datetime(j_now.year, j_now.month + 1, 1, 0, 0, 0)

        start_g_naive = start_j.togregorian()
        next_g_naive = next_j.togregorian()

        start = start_g_naive.replace(tzinfo=now.tzinfo)
        end = next_g_naive.replace(tzinfo=now.tzinfo)
        return start, end

    def _get_user_sessions_between(
        self,
        telegram_id: int,
        start: datetime,
        end: datetime,
    ) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, telegram_id, check_in, check_out
                FROM sessions
                WHERE telegram_id = ?
                  AND check_in >= ?
                  AND check_in < ?
                ORDER BY check_in ASC
                """,
                (telegram_id, start.isoformat(), end.isoformat()),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_current_jalali_month_sessions(
        self,
        telegram_id: int,
        now: datetime,
    ) -> list[dict]:
        start, end = self._jalali_month_bounds(now)
        return self._get_user_sessions_between(telegram_id, start, end)

    def get_current_jalali_month_sessions_with_user(
        self,
        telegram_id: int,
        now: datetime,
    ) -> list[dict]:
        start, end = self._jalali_month_bounds(now)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    s.id,
                    s.telegram_id,
                    u.name,
                    u.username,
                    s.check_in,
                    s.check_out
                FROM sessions AS s
                JOIN users AS u
                  ON u.telegram_id = s.telegram_id
                WHERE s.telegram_id = ?
                  AND s.check_in >= ?
                  AND s.check_in < ?
                ORDER BY s.check_in ASC
                """,
                (telegram_id, start.isoformat(), end.isoformat()),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_current_jalali_month_sessions(
        self,
        now: datetime,
    ) -> list[dict]:
        start, end = self._jalali_month_bounds(now)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    s.id,
                    s.telegram_id,
                    u.name,
                    u.username,
                    s.check_in,
                    s.check_out
                FROM sessions AS s
                JOIN users AS u
                  ON u.telegram_id = s.telegram_id
                WHERE s.check_in >= ?
                  AND s.check_in < ?
                ORDER BY s.check_in ASC
                """,
                (start.isoformat(), end.isoformat()),
            ).fetchall()
            return [dict(r) for r in rows]
