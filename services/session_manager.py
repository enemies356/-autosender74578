"""
services/session_manager.py
Управляет живыми Pyrogram-клиентами (user side).

При старте бота вызывается load_all_sessions(), которая восстанавливает
все сессии из БД. При падении бота при следующем запуске всё поднимается снова
— никаких .session-файлов и никакого active_clients = {}.
"""
import logging
from pyrogram import Client
from config import API_ID, API_HASH
from database.db import get_all_sessions, save_session, delete_session

log = logging.getLogger(__name__)

# Единственный источник правды о живых клиентах — этот словарь.
_clients: dict[int, Client] = {}


# ── Старт: восстановление всех сессий ────────────────────────────────────────

async def load_all_sessions() -> None:
    """Вызывается один раз при запуске main()."""
    rows = await get_all_sessions()
    for user_id, session_string in rows:
        try:
            client = Client(
                name=str(user_id),
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_string,
            )
            await client.start()
            _clients[user_id] = client
            log.info("Сессия восстановлена: user_id=%d", user_id)
        except Exception as exc:
            log.warning("Не удалось восстановить сессию user_id=%d: %s", user_id, exc)
            await delete_session(user_id)


# ── Auth-flow helpers ─────────────────────────────────────────────────────────

async def create_temp_client(user_id: int) -> Client:
    """
    Создаёт in-memory клиент для процесса авторизации.
    Никаких .session-файлов — сессия хранится только в ОЗУ до persist_client().
    """
    client = Client(
        name=str(user_id),
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True,
    )
    await client.connect()
    return client


async def persist_client(user_id: int, client: Client) -> None:
    """
    После успешной авторизации: экспортируем строку сессии в БД
    и регистрируем клиент как активный.
    """
    session_string = await client.export_session_string()
    await save_session(user_id, session_string)
    _clients[user_id] = client
    log.info("Сессия сохранена: user_id=%d", user_id)


# ── Доступ к клиентам ─────────────────────────────────────────────────────────

def get_client(user_id: int) -> Client | None:
    return _clients.get(user_id)


def is_authorized(user_id: int) -> bool:
    return user_id in _clients
