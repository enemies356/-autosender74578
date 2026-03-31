"""
main.py — точка входа.
Порядок: init_db → bot.start() → load_all_sessions → idle.
"""
import asyncio
import logging

from pyrogram  import idle

from database.db import init_db
from services.session_manager import load_all_sessions

# Регистрируем все хендлеры (декораторы срабатывают при импорте)
import handlers.auth     # noqa: F401
import handlers.template # noqa: F401
import handlers.send     # noqa: F401
import handlers.admin    # noqa: F401
import handlers.profile  # noqa: F401

from app import bot


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    await init_db()
    await bot.start()
    await load_all_sessions()

    logging.info("Бот авто-рассылки запущен. Ожидаю сообщения...")
    await idle()
    await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
