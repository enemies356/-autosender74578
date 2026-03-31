"""handlers/profile.py — кнопка «Профиль / Статус»."""
from pyrogram import Client, filters

from app import bot
from database.db import get_role, get_template
from services.session_manager import is_authorized
from handlers.keyboards import main_kb


@bot.on_callback_query(filters.regex(r"^profile$"))
async def cb_profile(client: Client, callback):
    user_id = callback.from_user.id
    role = await get_role(user_id)
    template = await get_template(user_id)
    authorized = is_authorized(user_id)

    text = (
        f"⚙️ <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🎭 Роль: {role or '—'}\n"
        f"🔑 Сессия: {'✅ Активна' if authorized else '❌ Не авторизован'}\n"
        f"📝 Шаблон: {'✅ Задан' if template else '❌ Не задан'}"
    )
    await callback.message.edit_text(text, parse_mode="html", reply_markup=main_kb())
    await callback.answer()
