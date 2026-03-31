"""handlers/auth.py — авторизация через Pyrogram (StringSession)."""
import logging
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired

from app import bot, fsm, state_filter
from database.db import get_role
from services.session_manager import create_temp_client, persist_client, is_authorized
from handlers.keyboards import main_kb

log = logging.getLogger(__name__)


# ── /start ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, message):
    user_id = message.from_user.id
    role = await get_role(user_id)

    if not role:
        await message.reply("❌ У вас нет доступа к боту.")
        return

    if is_authorized(user_id):
        await message.reply(
            "✅ <b>Добро пожаловать!</b>\n\nВыберите действие:",
            parse_mode="html",
            reply_markup=main_kb(),
        )
    else:
        fsm.set_state(user_id, "auth:phone")
        await message.reply(
            "👋 Привет! Для работы нужно авторизовать аккаунт Telegram.\n\n"
            "Отправь номер телефона в формате:\n"
            "<code>+79161234567</code>",
            parse_mode="html",
        )


# ── Шаг 1: телефон ───────────────────────────────────────────────────────────

@bot.on_message(state_filter("auth:phone") & filters.private & filters.text)
async def got_phone(client: Client, message):
    user_id = message.from_user.id
    phone = message.text.strip()

    status = await message.reply("⏳ Подключаюсь к Telegram...")
    try:
        temp_client = await create_temp_client(user_id)
        sent = await temp_client.send_code(phone)

        fsm.update_data(
            user_id,
            phone=phone,
            client=temp_client,
            phone_code_hash=sent.phone_code_hash,
        )
        fsm.set_state(user_id, "auth:code")

        await status.edit_text(
            "✅ Код отправлен в приложение Telegram.\n\n"
            "⚠️ <b>Важно:</b> отправь его <b>с пробелами</b> между цифрами,\n"
            "чтобы Telegram не пометил сообщение как переслан код.\n\n"
            "Пример: <code>1 2 3 4 5</code>",
            parse_mode="html",
        )
    except Exception as exc:
        log.exception("Ошибка при запросе кода для user_id=%d", user_id)
        await status.edit_text(f"❌ Ошибка подключения: {exc}")
        fsm.clear(user_id)


# ── Шаг 2: код ───────────────────────────────────────────────────────────────

@bot.on_message(state_filter("auth:code") & filters.private & filters.text)
async def got_code(client: Client, message):
    user_id = message.from_user.id
    code = "".join(c for c in message.text if c.isdigit())

    if not (4 <= len(code) <= 10):
        await message.reply(
            "Код выглядит неверно. Пришли его с пробелами: <code>1 2 3 4 5</code>",
            parse_mode="html",
        )
        return

    data = fsm.get_data(user_id)
    temp_client: Client = data.get("client")
    if not temp_client:
        await message.reply("⚠️ Сессия потеряна. Начни заново — /start")
        fsm.clear(user_id)
        return

    try:
        await temp_client.sign_in(data["phone"], data["phone_code_hash"], code)
        await persist_client(user_id, temp_client)
        fsm.clear(user_id)
        await message.reply("✅ Авторизация прошла успешно!", reply_markup=main_kb())

    except SessionPasswordNeeded:
        fsm.set_state(user_id, "auth:password")
        await message.reply("🔐 Введите пароль двухфакторной аутентификации (2FA):")

    except (PhoneCodeInvalid, PhoneCodeExpired):
        await message.reply(
            "❌ Код недействителен или истёк.\n"
            "Попробуй ещё раз или начни заново /start"
        )

    except Exception as exc:
        await message.reply(f"Ошибка при входе: {exc}")


# ── Шаг 3: пароль 2FA ────────────────────────────────────────────────────────

@bot.on_message(state_filter("auth:password") & filters.private & filters.text)
async def got_password(client: Client, message):
    user_id = message.from_user.id
    data = fsm.get_data(user_id)
    temp_client: Client = data.get("client")

    if not temp_client:
        await message.reply("⚠️ Сессия потеряна. Начни заново — /start")
        fsm.clear(user_id)
        return

    try:
        await temp_client.check_password(message.text.strip())
        await persist_client(user_id, temp_client)
        fsm.clear(user_id)
        await message.reply("✅ Авторизация с 2FA завершена!", reply_markup=main_kb())
    except Exception as exc:
        await message.reply(f"❌ Неверный пароль: {exc}")


# ── Fallback для неизвестных сообщений ───────────────────────────────────────

@bot.on_message(filters.private & filters.text)
async def fallback(client: Client, message):
    if message.text and message.text.startswith("/"):
        return
    state = fsm.get_state(message.from_user.id)
    if state is None:
        await message.reply(
            "Воспользуйтесь командой /start для открытия главного меню.",
            reply_markup=main_kb(),
        )
