import os
import aiosqlite
from typing import Optional, Tuple
from ig_monitor.config import get_settings


_settings = get_settings()
DB_PATH = os.path.join(_settings.data_dir, _settings.state_db_name)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


async def init_state() -> None:
    os.makedirs(_settings.data_dir, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(SCHEMA_SQL)
        await db.commit()


async def _get(key: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM app_state WHERE key=?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def _set(key: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO app_state(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await db.commit()


async def get_last_seen_id() -> Optional[str]:
    return await _get("last_seen_id")


async def set_last_seen_id(message_id: str) -> None:
    await _set("last_seen_id", message_id)


async def is_running() -> bool:
    return (await _get("is_running")) == "1"


async def set_running(running: bool) -> None:
    await _set("is_running", "1" if running else "0")


async def get_last_login_ts() -> Optional[str]:
    return await _get("last_login_ts")


async def set_last_login_ts(ts_iso: str) -> None:
    await _set("last_login_ts", ts_iso)


