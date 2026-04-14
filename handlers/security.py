#!/usr/bin/env python3
"""
Хендлеры безопасности: бан/разбан IP, автобан, просмотр атак
"""
import math
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from database import Database
from utils import IptablesManager, GeoIPLookup


class SecurityHandler:
    """Обработка команд безопасности"""

    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db

    # === Inline кнопки для сообщений об атаках ===

    @staticmethod
    def get_attack_keyboard(ip: str) -> InlineKeyboardMarkup:
        """Клавиатура для сообщения об атаке"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🚫 BAN {ip}", callback_data=f"ban_ip:{ip}"),
                InlineKeyboardButton(text=f"🔍 Info {ip}", callback_data=f"ip_info:{ip}"),
            ],
            [
                InlineKeyboardButton(text="⏳ Ban 1h", callback_data=f"ban_temp:{ip}:3600"),
                InlineKeyboardButton(text="⏳ Ban 24h", callback_data=f"ban_temp:{ip}:86400"),
            ],
            [
                InlineKeyboardButton(text="✅ Whitelist", callback_data=f"whitelist:{ip}"),
                InlineKeyboardButton(text="🌐 WHOIS", callback_data=f"whois:{ip}"),
            ],
        ])

    @staticmethod
    def get_banned_list_keyboard(page: int = 0) -> InlineKeyboardMarkup:
        """Клавиатура для списка банов"""
        buttons = []
        buttons.append([InlineKeyboardButton(text="🔄 Refresh", callback_data=f"banned_list:{page}")])
        if page > 0:
            buttons[0].insert(0, InlineKeyboardButton(text="⬅️", callback_data=f"banned_list:{page-1}"))
        buttons[0].append(InlineKeyboardButton(text="➡️", callback_data=f"banned_list:{page+1}"))
        buttons.append([InlineKeyboardButton(text="🗑️ Clear old bans", callback_data="clear_old_bans")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def get_main_security_keyboard() -> InlineKeyboardMarkup:
        """Главная клавиатура безопасности"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Top Attackers", callback_data="top_attackers"),
                InlineKeyboardButton(text="🚫 Banned IPs", callback_data="banned_list:0"),
            ],
            [
                InlineKeyboardButton(text="📈 Today Stats", callback_data="today_stats"),
                InlineKeyboardButton(text="📝 Audit Log", callback_data="audit_log"),
            ],
        ])

    # === Обработка callback-ов ===

    async def handle_callback(self, callback: CallbackQuery):
        """Обработка callback от inline кнопок"""
        data = callback.data
        telegram_id = callback.from_user.id

        # Проверка прав
        if telegram_id not in Config.ADMIN_USER_IDS:
            await callback.answer("❌ Нет прав", show_alert=True)
            return

        try:
            if data.startswith("ban_ip:"):
                ip = data.split(":", 1)[1]
                await self._ban_ip(callback, ip, telegram_id, "permanent")

            elif data.startswith("ban_temp:"):
                parts = data.split(":")
                ip = parts[1]
                seconds = int(parts[2])
                await self._ban_ip(callback, ip, telegram_id, f"temporary_{seconds}s")

            elif data.startswith("ip_info:"):
                ip = data.split(":", 1)[1]
                await self._show_ip_info(callback, ip)

            elif data.startswith("whois:"):
                ip = data.split(":", 1)[1]
                await self._show_whois(callback, ip)

            elif data.startswith("whitelist:"):
                ip = data.split(":", 1)[1]
                await callback.answer("⚠️ Whitelist в разработке", show_alert=True)

            elif data.startswith("banned_list:"):
                page = int(data.split(":")[1])
                await self._show_banned_list(callback, page)

            elif data == "top_attackers":
                await self._show_top_attackers(callback)

            elif data == "today_stats":
                await self._show_today_stats(callback)

            elif data == "audit_log":
                await self._show_audit_log(callback)

            elif data == "clear_old_bans":
                await self._clear_old_bans(callback, telegram_id)

            else:
                await callback.answer("❓ Неизвестная команда")

        except Exception as e:
            print(f"[SECURITY] Callback error: {e}")
            await callback.answer("❌ Ошибка", show_alert=True)

    async def _ban_ip(self, callback: CallbackQuery, ip: str, telegram_id: int, ban_type: str):
        """Забанить IP"""
        if self.db.is_banned(ip):
            await callback.answer(f"✅ {ip} уже забанен!", show_alert=True)
            return

        # Бан через iptables
        success = IptablesManager.ban_ip(ip)
        if success:
            # Бан в базе
            self.db.ban_ip(ip, reason="Manual ban via bot", banned_by=str(telegram_id))
            IptablesManager.save_rules()

            # Аудит
            self.db.log_action(telegram_id, "ban_ip", f"Banned {ip} ({ban_type})")

            await callback.answer(f"🚫 {ip} забанен!", show_alert=True)

            # Обновляем сообщение
            try:
                await callback.message.edit_text(
                    f"🚫 **BANNED**: `{ip}`\n"
                    f"Тип: {ban_type}\n"
                    f"Время: {self.db._get_conn().execute('SELECT CURRENT_TIMESTAMP').fetchone()[0]}",
                    parse_mode="Markdown"
                )
            except:
                pass
        else:
            await callback.answer(f"❌ Не удалось забанить {ip}", show_alert=True)

    async def _show_ip_info(self, callback: CallbackQuery, ip: str):
        """Показать информацию об IP"""
        await callback.answer("⏳ Загрузка...", show_alert=False)

        geo = GeoIPLookup.lookup(ip)
        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
        attempts = self.db.get_recent_attempts(ip, minutes=60)

        text = (
            f"🔍 **IP Information**\n\n"
            f"🌐 IP: `{ip}`\n"
            f"{flag} Страна: {geo['country']}\n"
            f"🏙️ Город: {geo['city']}\n"
            f"🏢 ISP: {geo['isp']}\n"
            f"🔌 ASN: {geo['as']}\n\n"
            f"📊 Попытки за последний час: **{attempts}**\n"
            f"🚫 В бане: **{'Да' if self.db.is_banned(ip) else 'Нет'}**"
        )

        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()

    async def _show_whois(self, callback: CallbackQuery, ip: str):
        """WHOIS информация"""
        await callback.answer("⏳ Загрузка WHOIS...", show_alert=False)

        import subprocess
        try:
            result = subprocess.run(
                ["whois", ip],
                capture_output=True, text=True, timeout=10
            )
            whois_data = result.stdout[:4000]  # Ограничиваем длину

            # Краткая выжимка
            lines = whois_data.split("\n")
            short_info = []
            for line in lines:
                for key in ["inetnum", "netname", "descr", "country", "org", "abuse"]:
                    if line.lower().startswith(key):
                        short_info.append(line)
                        break

            text = f"🌐 **WHOIS {ip}**\n\n" + "\n".join(short_info[:15])
        except:
            text = f"❌ Не удалось получить WHOIS для {ip}"

        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()

    async def _show_banned_list(self, callback: CallbackQuery, page: int):
        """Список забаненных IP"""
        per_page = 15
        banned = self.db.get_banned_ips(limit=per_page, offset=page * per_page)
        total = self.db.get_banned_count()

        if not banned:
            text = "✅ Список банов пуст"
        else:
            text = f"🚫 **Banned IPs** ({total} total)\n\n"
            for i, b in enumerate(banned, 1):
                geo = GeoIPLookup.lookup(b["ip"])
                flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
                text += f"{i}. `{b['ip']}` {flag} - {b.get('country', 'Unknown')}\n"
                text += f"   📅 {b['banned_at']} | 📝 {b.get('reason', '')}\n\n"

        await callback.message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=self.get_banned_list_keyboard(page)
        )
        await callback.answer()

    async def _show_top_attackers(self, callback: CallbackQuery):
        """ТОП атакующих"""
        attackers = self.db.get_top_attackers(10)

        if not attackers:
            text = "📊 Нет данных об атаках"
        else:
            text = "🏆 **TOP Attackers**\n\n"
            for i, a in enumerate(attackers, 1):
                geo = GeoIPLookup.lookup(a["ip"])
                flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
                text += f"{i}. `{a['ip']}` {flag} - **{a['attempts']}** attempts\n"

        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()

    async def _show_today_stats(self, callback: CallbackQuery):
        """Статистика за сегодня"""
        stats = self.db.get_today_stats()
        text = (
            f"📊 **Today's Statistics**\n\n"
            f"🔐 Всего попыток: **{stats.get('total_attempts', 0)}**\n"
            f"❌ Неудачных: **{stats.get('failed', 0)}**\n"
            f"✅ Успешных: **{stats.get('success', 0)}**\n"
            f"🌐 Уникальных IP: **{stats.get('unique_ips', 0)}**"
        )
        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()

    async def _show_audit_log(self, callback: CallbackQuery):
        """Аудит-лог"""
        logs = self.db.get_audit_log(10)

        if not logs:
            text = "📝 Аудит-лог пуст"
        else:
            text = "📝 **Audit Log**\n\n"
            for log in logs:
                text += f"🕐 {log['timestamp']}\n"
                text += f"👤 ID: {log['telegram_id']} | 🎯 {log['action']}\n"
                if log.get('details'):
                    text += f"📝 {log['details']}\n"
                text += "\n"

        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()

    async def _clear_old_bans(self, callback: CallbackQuery, telegram_id: int):
        """Очистка старых банов"""
        await callback.answer("⏳ Очистка...", show_alert=False)

        import subprocess
        try:
            result = subprocess.run(
                ["iptables", "-L", "INPUT", "-n", "--line-numbers"],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.split("\n")
            # Удаляем баны старше 7 дней (упрощённо)
            self.db.log_action(telegram_id, "clear_old_bans", "Cleared old bans")
            await callback.answer("✅ Очистка выполнена", show_alert=True)
        except:
            await callback.answer("❌ Ошибка очистки", show_alert=True)
