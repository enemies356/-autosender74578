"""handlers/admin.py — управление доступом (owner/admin)."""
from pyrogram import Client, filters

from app import bot, fsm, state_filter
from database.db import get_role, upsert_user, delete_user, get_users_by_role
from handlers.keyboards import admin_kb, main_kb


# ── /admin ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("admin") & filters.private)
async def cmd_admin(client: Client, message):
    user_id = message.from_user.id
    role = await get_role(user_id)
    if role not in ("owner", "admin"):
        await message.reply("❌ У вас нет доступа к панели управления.")
        return
    await message.reply(
        f"👑 <b>Панель управления</b>\n🎭 Ваша роль: <b>{role.capitalize()}</b>",
        parse_mode="html",
        reply_markup=admin_kb(role),
    )


# ── Callback-роутер ───────────────────────────────────────────────────────────

_PROMPTS = {
    "add_admin": ("owner",  "adm:add_admin", "Введите Telegram ID нового <b>Админа</b>:"),
    "del_admin": ("owner",  "adm:del_admin", "Введите Telegram ID <b>Админа</b> для удаления:"),
    "add_user":  (None,     "adm:add_user",  "Введите Telegram ID нового <b>Пользователя</b>:"),
    "del_user":  (None,     "adm:del_user",  "Введите Telegram ID <b>Пользователя</b> для удаления:"),
}


@bot.on_callback_query(filters.regex(r"^adm:"))
async def admin_callbacks(client: Client, callback):
    user_id = callback.from_user.id
    role = await get_role(user_id)
    if role not in ("owner", "admin"):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    action = callback.data.split(":", 1)[1]

    if action == "list":
        await _show_list(callback, role)
    elif action in _PROMPTS:
        required_role, state, prompt = _PROMPTS[action]
        if required_role and role != required_role:
            await callback.answer("Только владелец может это делать.", show_alert=True)
            return
        fsm.set_state(user_id, state)
        await callback.message.edit_text(prompt, parse_mode="html")

    await callback.answer()


async def _show_list(callback, role: str) -> None:
    lines = ["📋 <b>Список доступов:</b>\n"]
    if role == "owner":
        admins = await get_users_by_role("admin")
        adm_str = "\n".join(
            f"  • <code>{uid}</code>  @{uname or '—'}" for uid, uname in admins
        ) or "  —"
        lines.append(f"👮 <b>Админы:</b>\n{adm_str}\n")

    users = await get_users_by_role("user")
    usr_str = "\n".join(
        f"  • <code>{uid}</code>  @{uname or '—'}" for uid, uname in users
    ) or "  —"
    lines.append(f"👤 <b>Пользователи:</b>\n{usr_str}")

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="html",
        reply_markup=admin_kb(role),
    )


# ── Общий валидатор ID ────────────────────────────────────────────────────────

def _parse_id(text: str) -> int | None:
    return int(text.strip()) if text.strip().isdigit() else None


# ── State-хендлеры (добавление/удаление) ─────────────────────────────────────

@bot.on_message(state_filter("adm:add_admin") & filters.private & filters.text)
async def adm_add_admin(client: Client, message):
    uid = _parse_id(message.text)
    if not uid:
        await message.reply("ID должен состоять только из цифр.")
        return
    await upsert_user(uid, "admin")
    fsm.clear(message.from_user.id)
    await message.reply(
        f"✅ <code>{uid}</code> добавлен как <b>Админ</b>.",
        parse_mode="html",
        reply_markup=main_kb(),
    )


@bot.on_message(state_filter("adm:del_admin") & filters.private & filters.text)
async def adm_del_admin(client: Client, message):
    uid = _parse_id(message.text)
    if not uid:
        await message.reply("ID должен состоять только из цифр.")
        return
    ok = await delete_user(uid)
    fsm.clear(message.from_user.id)
    result = f"✅ Удалён: <code>{uid}</code>" if ok else f"❌ Не найден: <code>{uid}</code>"
    await message.reply(result, parse_mode="html", reply_markup=main_kb())


@bot.on_message(state_filter("adm:add_user") & filters.private & filters.text)
async def adm_add_user(client: Client, message):
    uid = _parse_id(message.text)
    if not uid:
        await message.reply("ID должен состоять только из цифр.")
        return
    await upsert_user(uid, "user")
    fsm.clear(message.from_user.id)
    await message.reply(
        f"✅ <code>{uid}</code> добавлен как <b>Пользователь</b>.",
        parse_mode="html",
        reply_markup=main_kb(),
    )


@bot.on_message(state_filter("adm:del_user") & filters.private & filters.text)
async def adm_del_user(client: Client, message):
    uid = _parse_id(message.text)
    if not uid:
        await message.reply("ID должен состоять только из цифр.")
        return
    ok = await delete_user(uid)
    fsm.clear(message.from_user.id)
    result = f"✅ Удалён: <code>{uid}</code>" if ok else f"❌ Не найден: <code>{uid}</code>"
    await message.reply(result, parse_mode="html", reply_markup=main_kb())
