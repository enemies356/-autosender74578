"""handlers/keyboards.py — все клавиатуры в одном месте."""
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Шаблон",   callback_data="tpl:edit"),
            InlineKeyboardButton("🚀 Рассылка", callback_data="send:start"),
        ],
        [
            InlineKeyboardButton("⚙️ Профиль / Статус", callback_data="profile"),
        ],
    ])


def admin_kb(role: str) -> InlineKeyboardMarkup:
    rows = []
    if role == "owner":
        rows.append([
            InlineKeyboardButton("➕ Добавить Админа", callback_data="adm:add_admin"),
            InlineKeyboardButton("❌ Удалить Админа",  callback_data="adm:del_admin"),
        ])
    rows.append([
        InlineKeyboardButton("➕ Добавить Юзера", callback_data="adm:add_user"),
        InlineKeyboardButton("❌ Удалить Юзера",  callback_data="adm:del_user"),
    ])
    rows.append([
        InlineKeyboardButton("📋 Список пользователей", callback_data="adm:list"),
    ])
    return InlineKeyboardMarkup(rows)


def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Запустить", callback_data="send:confirm"),
        InlineKeyboardButton("❌ Отмена",    callback_data="send:cancel"),
    ]])
