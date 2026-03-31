"""handlers/template.py — сохранение шаблона рассылки."""
from pyrogram import Client, filters

from app import bot, fsm, state_filter
from database.db import save_template
from services.session_manager import is_authorized
from handlers.keyboards import main_kb


@bot.on_callback_query(filters.regex(r"^tpl:edit$"))
async def cb_template_edit(client: Client, callback):
    user_id = callback.from_user.id
    if not is_authorized(user_id):
        await callback.answer("Сначала авторизуйся через /start", show_alert=True)
        return
    fsm.set_state(user_id, "template:waiting")
    await callback.message.edit_text(
        "📝 Отправь новый текст шаблона сообщения.\n\n"
        "Это то, что будет отправлено каждому получателю."
    )
    await callback.answer()


@bot.on_message(state_filter("template:waiting") & filters.private & filters.text)
async def got_template(client: Client, message):
    user_id = message.from_user.id
    await save_template(user_id, message.text)
    fsm.clear(user_id)
    await message.reply(
        f"✅ <b>Шаблон сохранён:</b>\n\n{message.text}",
        parse_mode="html",
        reply_markup=main_kb(),
    )
