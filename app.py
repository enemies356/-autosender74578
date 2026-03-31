"""
app.py — единственное место, где создаётся экземпляр бота.
Импортируй `bot` и `fsm` во всех хендлерах.
"""
from pyrogram import Client, filters as pyro_filters
from config import BOT_TOKEN, API_ID, API_HASH

bot = Client(
    name="mybot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
)


# ── Простой FSM (in-memory) ───────────────────────────────────────────────────
class _FSM:
    """Хранит состояние и данные для каждого пользователя."""

    def __init__(self):
        self._states: dict[int, str] = {}
        self._data: dict[int, dict] = {}

    def get_state(self, uid: int) -> str | None:
        return self._states.get(uid)

    def set_state(self, uid: int, state: str) -> None:
        self._states[uid] = state
        self._data.setdefault(uid, {})

    def clear(self, uid: int) -> None:
        self._states.pop(uid, None)
        self._data.pop(uid, None)

    def update_data(self, uid: int, **kwargs) -> None:
        self._data.setdefault(uid, {}).update(kwargs)

    def get_data(self, uid: int) -> dict:
        return self._data.get(uid, {})


fsm = _FSM()


def state_filter(state: str):
    """Кастомный Pyrogram-фильтр: пропускает только нужное состояние."""
    async def _check(_, __, message):
        return fsm.get_state(message.from_user.id) == state

    return pyro_filters.create(_check)
