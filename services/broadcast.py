"""
services/broadcast.py
Рассылка запускается через asyncio.create_task() и НЕ блокирует бота.
Прогресс отправляется пользователю через bot.send_message().
"""
import asyncio
import logging
import re

from pyrogram import Client
from pyrogram.errors import FloodWait, PeerFlood, UsernameNotOccupied, UsernameInvalid

log = logging.getLogger(__name__)


def parse_usernames(raw: str) -> list[str]:
    """Принимает любой формат: запятые, пробелы, переносы, @-префикс."""
    parts = re.split(r"[,\s\n]+", raw.strip())
    return [p.lstrip("@").strip(".") for p in parts if p.strip()]


async def run_broadcast(
    owner_id: int,
    user_client: Client,
    usernames: list[str],
    template: str,
) -> None:
    """
    Фоновая задача. Отправляет сообщения и репортует прогресс в личку.
    Не импортируем `bot` здесь напрямую во избежание циклических зависимостей —
    передаём его снаружи.
    """
    from app import bot  # отложенный импорт

    sent = skipped = 0
    total = len(usernames)

    await bot.send_message(owner_id, f"🚀 Рассылка запущена: {total} получателей.")

    for username in usernames:
        try:
            await user_client.send_message(username, template)
            sent += 1
            await bot.send_message(owner_id, f"✅ @{username}")
            await asyncio.sleep(2)  # антифлуд-задержка

        except FloodWait as e:
            wait = e.value + 5
            await bot.send_message(owner_id, f"⏳ FloodWait — жду {wait} сек...")
            await asyncio.sleep(wait)
            # Повторная попытка после ожидания
            try:
                await user_client.send_message(username, template)
                sent += 1
                await bot.send_message(owner_id, f"✅ @{username} (повтор)")
            except Exception:
                skipped += 1

        except PeerFlood:
            await bot.send_message(
                owner_id,
                "🚫 PeerFlood! Аккаунт временно ограничен Telegram.\n"
                "Рассылка остановлена для защиты аккаунта.",
            )
            break

        except (UsernameNotOccupied, UsernameInvalid):
            skipped += 1
            await bot.send_message(owner_id, f"❌ @{username} — не найден")

        except Exception as exc:
            skipped += 1
            log.warning("Ошибка при отправке @%s: %s", username, exc)
            await bot.send_message(owner_id, f"⚠️ @{username} — {str(exc)[:80]}")

    await bot.send_message(
        owner_id,
        f"🎉 Готово!\n"
        f"✅ Отправлено: {sent}\n"
        f"❌ Пропущено: {skipped}\n"
        f"📊 Всего: {total}",
    )
