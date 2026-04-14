#!/usr/bin/env python3
"""
Хендлеры администратора: /start, /status, /commands и другие
"""
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import Config, PANELS
from database import Database
from monitors.system_monitor import SystemMonitor
from monitors.docker_monitor import DockerMonitor
from utils import IptablesManager, GeoIPLookup


class AdminHandler:
    """Обработка админ-команд"""

    def __init__(self, bot, db: Database, sys_monitor: SystemMonitor, docker_monitor: DockerMonitor):
        self.bot = bot
        self.db = db
        self.sys_monitor = sys_monitor
        self.docker_monitor = docker_monitor

    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Главная клавиатура"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Status", callback_data="status"),
                InlineKeyboardButton(text="🔒 Security", callback_data="security_menu"),
            ],
            [
                InlineKeyboardButton(text="👥 Users", callback_data="users_menu"),
                InlineKeyboardButton(text="🐳 Docker", callback_data="docker_menu"),
            ],
            [
                InlineKeyboardButton(text="📈 Reports", callback_data="reports_menu"),
                InlineKeyboardButton(text="⚙️ Settings", callback_data="settings_menu"),
            ],
        ])

    async def cmd_start(self, message: types.Message):
        """Команда /start"""
        telegram_id = message.from_user.id

        if telegram_id not in Config.ADMIN_USER_IDS:
            await message.answer("❌ У вас нет доступа к этому боту.")
            return

        # Сохраняем пользователя
        self.db.save_user_settings(telegram_id, message.from_user.username, Config.LANGUAGE)

        text = (
            f"👋 **Добро пожаловать, {message.from_user.first_name}!**\n\n"
            f"🛡️ **Marzban Security Bot v3**\n"
            f"Полный контроль безопасности и управления сервером\n\n"
            f"📋 **Возможности:**\n"
            f"🔐 Мониторинг попыток входа\n"
            f"🚫 Бан/разбан IP\n"
            f"📊 Статистика и отчёты\n"
            f"👥 Управление пользователями\n"
            f"🐳 Управление Docker\n"
            f"💾 Бэкапы\n\n"
            f"Выберите раздел ниже 👇"
        )

        await message.answer(text, parse_mode="Markdown", reply_markup=self.get_main_keyboard())

    async def cmd_status(self, message: types.Message):
        """Команда /status"""
        await self._send_status(message)

    async def cmd_help(self, message: types.Message):
        """Команда /help"""
        text = (
            f"📖 **Справка по командам**\n\n"
            f"/start - Главное меню\n"
            f"/status - Статус сервера\n"
            f"/security - Меню безопасности\n"
            f"/users - Пользователи Marzban\n"
            f"/docker - Docker контейнеры\n"
            f"/backup - Создать бэкап\n"
            f"/banned - Список забаненных\n"
            f"/unban <ip> - Разбанить IP\n"
            f"/logs [n] - Последние N логов\n"
            f"/connections - Активные соединения\n"
            f"/reports - Отчёты\n"
            f"/help - Эта справка"
        )
        await message.answer(text, parse_mode="Markdown")

    async def cmd_banned(self, message: types.Message):
        """Команда /banned"""
        from handlers.security import SecurityHandler
        handler = SecurityHandler(self.bot, self.db)

        # Создаём фейковый callback для переиспользования
        class FakeCallback:
            def __init__(self, msg):
                self.message = msg
                self.data = "banned_list:0"
                self.from_user = msg.from_user
                self.answer = lambda *a, **k: None

        await handler._show_banned_list(FakeCallback(message), 0)

    async def cmd_unban(self, message: types.Message):
        """Команда /unban <ip>"""
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Использование: `/unban <ip>`", parse_mode="Markdown")
            return

        ip = parts[1]

        # Разбан iptables
        IptablesManager.unban_ip(ip)
        self.db.unban_ip(ip, unbanned_by=str(message.from_user.id))
        IptablesManager.save_rules()

        # Аудит
        self.db.log_action(message.from_user.id, "unban_ip", f"Unbanned {ip}")

        await message.answer(f"✅ **{ip}** разбанен!", parse_mode="Markdown")

    async def cmd_connections(self, message: types.Message):
        """Команда /connections"""
        import subprocess
        try:
            # Топ IP по соединениям
            result = subprocess.run(
                "ss -tn state established | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -20",
                shell=True, capture_output=True, text=True, timeout=10
            )

            text = "🔌 **Active Connections**\n\n"
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n")[:20]:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        count, ip = parts[0], parts[1]
                        geo = GeoIPLookup.lookup(ip)
                        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
                        text += f"`{ip}` {flag} - **{count}** conn\n"
            else:
                text += "Нет данных"

            await message.answer(text, parse_mode="Markdown")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")

    async def cmd_logs(self, message: types.Message):
        """Команда /logs [n]"""
        parts = message.text.split()
        lines = int(parts[1]) if len(parts) > 1 else 50
        lines = min(lines, 200)  # Максимум 200

        import subprocess
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), "marzban-marzban-1"],
                capture_output=True, text=True, timeout=10
            )
            logs = (result.stdout + result.stderr).strip()

            if logs:
                # Ограничиваем длину сообщения
                if len(logs) > 4000:
                    logs = logs[-4000:]
                    logs = "...\n" + logs

                await message.answer(f"📝 **Последние {lines} строк лога:**\n\n```\n{logs}\n```", parse_mode="Markdown")
            else:
                await message.answer("📝 Логи пусты")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")

    async def cmd_backup(self, message: types.Message):
        """Команда /backup"""
        from utils import BackupManager

        await message.answer("⏳ Создание бэкапа...")

        backup_file = BackupManager.create_backup()
        if backup_file:
            size = os.path.getsize(backup_file)
            size_human = BackupManager._format_size(size)

            # Записываем в БД
            self.db.log_action(message.from_user.id, "backup", f"Created backup: {backup_file}")

            await message.answer(f"✅ Бэкап создан:\n📁 `{backup_file}`\n📦 Размер: {size_human}")

            # Отправляем файл (если не слишком большой)
            if size < 50 * 1024 * 1024:  # < 50MB
                with open(backup_file, "rb") as f:
                    await message.answer_document(f, caption=f"📦 Marzban Backup\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            else:
                await message.answer("⚠️ Файл слишком большой для отправки, сохранён на сервере")
        else:
            await message.answer("❌ Не удалось создать бэкап")

    async def _send_status(self, target, is_callback=False):
        """Отправить статус сервера"""
        # Системный статус
        sys_status = self.sys_monitor.get_full_status()

        # Docker статус
        containers = self.docker_monitor.get_containers_status()

        # Статистика безопасности
        banned_count = self.db.get_banned_count()
        today_attempts = self.db.get_attempts_today()

        # Формируем сообщение
        cpu = sys_status["cpu"]
        ram = sys_status["ram"]
        disk = sys_status["disk"]

        # CPU статус
        if cpu > 80:
            cpu_icon = "🔴"
        elif cpu > 50:
            cpu_icon = "🟡"
        else:
            cpu_icon = "🟢"

        # RAM статус
        if ram["percent"] > 80:
            ram_icon = "🔴"
        elif ram["percent"] > 50:
            ram_icon = "🟡"
        else:
            ram_icon = "🟢"

        text = (
            f"📊 **Server Status**\n\n"
            f"{cpu_icon} **CPU:** {cpu}%\n"
            f"{ram_icon} **RAM:** {ram['percent']}% ({self._format_bytes(ram['used'])} / {self._format_bytes(ram['total'])})\n"
            f"💾 **Disk:** {disk['percent']}% ({self._format_bytes(disk['used'])} / {self._format_bytes(disk['total'])})\n"
            f"🔌 **Connections:** {sys_status['connections']}\n"
            f"⏱️ **Uptime:** {sys_status['uptime']}\n\n"
            f"🐳 **Docker Containers:**\n"
        )

        for c in containers[:5]:
            icon = "✅" if c["running"] else "❌"
            text += f"{icon} `{c['name']}`\n"

        text += (
            f"\n🛡️ **Security:**\n"
            f"🚫 Banned IPs: {banned_count}\n"
            f"🔐 Failed attempts today: {today_attempts}\n"
        )

        # ТОП процессы
        if sys_status.get("top_processes"):
            text += f"\n🔝 **Top Processes:**\n"
            for proc in sys_status["top_processes"][:3]:
                text += f"• `{proc['name']}` - CPU: {proc['cpu']}%, RAM: {proc['mem']:.1f}%\n"

        # Клавиатура
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data="status"),
                InlineKeyboardButton(text="📈 Detailed", callback_data="detailed_status"),
            ],
        ])

        if is_callback:
            try:
                await target.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
            except:
                await target.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await target.answer(text, parse_mode="Markdown", reply_markup=keyboard)

    @staticmethod
    def _format_bytes(bytes_val: float) -> str:
        """Форматировать байты"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"


# Импорт нужен для cmd_backup
import os
from datetime import datetime
