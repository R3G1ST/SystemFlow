#!/usr/bin/env python3
"""
Хендлеры пользователей Marzban: просмотр, создание, управление
"""
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config, PANELS, PanelConfig
from database import Database
from utils import MarzbanAPI


class UsersHandler:
    """Управление пользователями Marzban"""

    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db

    async def cmd_users(self, message: types.Message):
        """Команда /users"""
        await message.answer("⏳ Загрузка пользователей...")

        users = await self._get_users()
        if not users:
            await message.answer("⚠️ Не удалось загрузить пользователей.\nНастройте API токен в .env")
            return

        text = f"👥 **Users ({len(users)})**\n\n"
        for user in users[:20]:  # Показываем первых 20
            status_icon = {
                "active": "✅",
                "disabled": "❌",
                "limited": "⚠️",
                "expired": "⌛",
            }.get(user.get("status", ""), "❓")

            name = user.get("username", "Unknown")
            data_used = user.get("used_traffic", 0)
            data_limit = user.get("data_limit", 0)

            traffic_str = self._format_traffic(data_used)
            if data_limit:
                traffic_str += f" / {self._format_traffic(data_limit)}"

            expire = user.get("expire")
            expire_str = self._format_expire(expire) if expire else "♾️"

            text += f"{status_icon} `{name}` - {traffic_str} - {expire_str}\n"

        if len(users) > 20:
            text += f"\n... и ещё {len(users) - 20} пользователей"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Add User", callback_data="add_user"),
                InlineKeyboardButton(text="🔄 Refresh", callback_data="users_menu"),
            ],
        ])

        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

    async def _get_users(self) -> list:
        """Получить пользователей"""
        for panel in PANELS:
            token = PanelConfig.get_panel_api_token(panel["name"])
            if token:
                api = MarzbanAPI(panel["url"], token)
                users = api.get_users()
                if users:
                    return users
        return []

    @staticmethod
    def _format_traffic(bytes_val: float) -> str:
        """Форматировать трафик"""
        if not bytes_val:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"

    @staticmethod
    def _format_expire(expire_timestamp) -> str:
        """Форматировать дату истечения"""
        from datetime import datetime
        try:
            expire_date = datetime.fromtimestamp(expire_timestamp)
            now = datetime.now()
            delta = expire_date - now
            days_left = delta.days

            if days_left < 0:
                return f"⌛ Expired"
            elif days_left == 0:
                return "⚠️ Today"
            elif days_left <= 7:
                return f"⚠️ {days_left}d"
            else:
                return f"{days_left}d"
        except:
            return "♾️"
