"""
database/db.py — три таблицы вместо .env.
  users     : user_id, username, role
  templates : user_id, content
  sessions  : user_id, session_string
"""
import aiosqlite
from config import DB_PATH


# ── Инициализация ─────────────────────────────────────────────────────────────

async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id  INTEGER PRIMARY KEY,
                username TEXT    DEFAULT '',
                role     TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS templates (
                user_id  INTEGER PRIMARY KEY,
                content  TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                user_id        INTEGER PRIMARY KEY,
                session_string TEXT    NOT NULL
            );
        """)
        await db.commit()


# ── Users ─────────────────────────────────────────────────────────────────────

async def get_role(user_id: int) -> str | None:
    from config import OWNER_IDS
    if user_id in OWNER_IDS:
        return "owner"
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def upsert_user(user_id: int, role: str, username: str = "") -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, role) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET role=excluded.role, username=excluded.username
            """,
            (user_id, username, role),
        )
        await db.commit()


async def delete_user(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()
        return cur.rowcount > 0


async def get_users_by_role(role: str) -> list[tuple[int, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username FROM users WHERE role = ?", (role,)
        ) as cur:
            return await cur.fetchall()


# ── Templates ─────────────────────────────────────────────────────────────────

async def get_template(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT content FROM templates WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def save_template(user_id: int, content: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO templates (user_id, content) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET content=excluded.content
            """,
            (user_id, content),
        )
        await db.commit()


# ── Sessions ──────────────────────────────────────────────────────────────────

async def save_session(user_id: int, session_string: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO sessions (user_id, session_string) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET session_string=excluded.session_string
            """,
            (user_id, session_string),
        )
        await db.commit()


async def get_session(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT session_string FROM sessions WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def delete_session(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_all_sessions() -> list[tuple[int, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, session_string FROM sessions") as cur:
            return await cur.fetchall()
