"""handlers/send.py — запуск рассылки (в фоне через asyncio.create_task)."""
import asyncio
from pyrogram import Client, filters

from app import bot, fsm, state_filter
from database.db import get_template
from services.session_manager import get_client, is_authorized
from services.broadcast import run_broadcast, parse_usernames
from handlers.keyboards import confirm_broadcast_kb, main_kb


@bot.on_callback_query(filters.regex(r"^send:start$"))
async def cb_send_start(client: Client, callback):
    user_id = callback.from_user.id

    if not is_authorized(user_id):
        await callback.answer("Сначала авторизуйся через /start", show_alert=True)
        return

    template = await get_template(user_id)
    if not template:
        await callback.answer("Сначала задай шаблон (📝 Шаблон)", show_alert=True)
        return

    await callback.message.edit_text(
        f"📋 <b>Текущий шаблон:</b>\n\n{template}\n\n"
        f"Запустить рассылку по этому шаблону?",
        parse_mode="html",
        reply_markup=confirm_broadcast_kb(),
    )
    await callback.answer()


@bot.on_callback_query(filters.regex(r"^send:confirm$"))
async def cb_send_confirm(client: Client, callback):
    user_id = callback.from_user.id
    fsm.set_state(user_id, "send:usernames")
    await callback.message.edit_text(
        "📨 Отправь список получателей.\n\n"
        "Форматы: <code>@username1 @username2</code> или через запятую/перенос строки.",
        parse_mode="html",
    )
    await callback.answer()


@bot.on_callback_query(filters.regex(r"^send:cancel$"))
async def cb_send_cancel(client: Client, callback):
    await callback.message.edit_text("❌ Рассылка отменена.", reply_markup=main_kb())
    await callback.answer()


@bot.on_message(state_filter("send:usernames") & filters.private & filters.text)
async def got_usernames(client: Client, message):
    user_id = message.from_user.id
    user_client = get_client(user_id)
    template = await get_template(user_id)

    if not user_client or not template:
        await message.reply("❌ Ошибка сессии или шаблон не найден. Начни заново /start")
        fsm.clear(user_id)
        return

    usernames = parse_usernames(message.text)
    if not usernames:
        await message.reply("Список пустой. Попробуй ещё раз.")
        return

    fsm.clear(user_id)

    # Рассылка — в фоне, бот не блокируется.
    asyncio.create_task(
        run_broadcast(user_id, user_client, usernames, template)
    )

    await message.reply(
        f"✅ Рассылка запущена в фоне на <b>{len(usernames)}</b> аккаунтов.\n"
        f"Прогресс будет приходить сюда.",
        parse_mode="html",
        reply_markup=main_kb(),
    )
