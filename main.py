import asyncio
import logging

from pyrogram import idle

# Импорты базы и сервисов
from database.db import init_db
from services.session_manager import load_all_sessions

# Регистрируем все хендлеры (декораторы @bot.on_... срабатывают при импорте модуля)
import handlers.auth      # noqa: F401
import handlers.template  # noqa: F401
import handlers.send      # noqa: F401
import handlers.admin     # noqa: F401
import handlers.profile   # noqa: F401

from app import bot        # ← твой основной Client


async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    logging.info("Инициализация базы данных...")
    await init_db()

    logging.info("Запуск основного клиента бота...")
    await bot.start()

    logging.info("Загрузка всех дополнительных сессий...")
    await load_all_sessions()

    logging.info("✅ Бот авто-рассылки успешно запущен. Ожидаю сообщения...")
    
    # idle() будет работать, пока не нажмёшь Ctrl+C
    await idle()

    # Корректное завершение
    logging.info("Остановка бота...")
    await bot.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Получен сигнал завершения (Ctrl+C). Бот остановлен.")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)
