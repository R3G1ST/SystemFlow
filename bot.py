#!/usr/bin/env python3
"""
Marzban Security Bot v3 - Главный файл
Универсальный бот для мониторинга и управления Marzban
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command

from config import Config, PANELS
from database import Database
from monitors.log_monitor import MultiPanelLogMonitor
from monitors.system_monitor import SystemMonitor
from monitors.docker_monitor import DockerMonitor
from handlers.admin import AdminHandler
from handlers.security import SecurityHandler
from handlers.users import UsersHandler
from handlers.reports import ReportGenerator
from utils import GeoIPLookup

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarzbanBot:
    """Основной класс бота"""

    def __init__(self):
        # Проверка токена
        if not Config.BOT_TOKEN or Config.BOT_TOKEN == "your_bot_token_here":
            print("❌ ОШИБКА: Не задан BOT_TOKEN в .env файле!")
            print("📝 Скопируйте .env.example в .env и настройте токен")
            exit(1)

        # Инициализация компонентов
        self.bot = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        self.dp = Dispatcher()

        self.db = Database()
        self.sys_monitor = SystemMonitor(check_interval=Config.SYSTEM_CHECK_INTERVAL)
        self.docker_monitor = DockerMonitor(
            check_interval=30,
            monitored_containers=[p["container"] for p in PANELS]
        )
        self.log_monitor = MultiPanelLogMonitor()
        self.report_gen = ReportGenerator(self.db)

        # Хендлеры
        self.admin_handler = AdminHandler(self.bot, self.db, self.sys_monitor, self.docker_monitor)
        self.security_handler = SecurityHandler(self.bot, self.db)
        self.users_handler = UsersHandler(self.bot, self.db)

        # Счётчик попыток для автобана
        self._pending_bans = {}

    def setup_callbacks(self):
        """Настройка callback-ов мониторинга"""

        # === Лог-монитор ===
        for panel in PANELS:
            monitor = self.log_monitor.add_panel(
                panel["container"],
                panel["name"],
                Config.MONITOR_INTERVAL
            )

            # 401 Unauthorized
            monitor.on("login_401", self._on_login_401)
            # Успешный вход
            monitor.on("login_200", self._on_login_200)

        # === Системный монитор ===
        if Config.NOTIFY_ON_HIGH_CPU:
            self.sys_monitor.on("high_cpu", self._on_high_cpu)
        if Config.NOTIFY_ON_HIGH_RAM:
            self.sys_monitor.on("high_ram", self._on_high_ram)
        if Config.NOTIFY_ON_HIGH_CPU:
            self.sys_monitor.on("high_connections", self._on_high_connections)

        # === Docker монитор ===
        self.docker_monitor.on("container_down", self._on_container_down)
        self.docker_monitor.on("container_restart", self._on_container_restart)

    async def _on_login_401(self, data: dict):
        """Обработка попытки входа"""
        ip = data["ip"]
        panel = data["panel"]

        # Логируем в БД
        geo = GeoIPLookup.lookup(ip)
        self.db.log_login_attempt(
            ip, success=False, status_code=401,
            panel_name=panel, country=geo.get("country")
        )

        # Проверяем автобан
        if Config.AUTOBAN_ENABLED:
            attempts = self.db.get_recent_attempts(ip, Config.BAN_TIME_WINDOW // 60)
            if attempts >= Config.MAX_LOGIN_ATTEMPTS and ip not in self._pending_bans:
                self._pending_bans[ip] = True
                await self._auto_ban_ip(ip, panel)

        # Отправляем уведомление
        if Config.NOTIFY_ON_401:
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text = (
                f"🚨 **Failed Login Attempt**\n\n"
                f"🌐 IP: `{ip}` {flag}\n"
                f"🌍 Country: {geo['country']} - {geo['city']}\n"
                f"🏢 ISP: {geo['isp']}\n"
                f"🖥️ Panel: {panel}\n"
                f"🕐 Time: {data['timestamp']}\n\n"
                f"⚠️ Попыток за последний час: **{self.db.get_recent_attempts(ip, 60)}**"
            )

            keyboard = self.security_handler.get_attack_keyboard(ip)

            for admin_id in Config.ADMIN_USER_IDS:
                try:
                    await self.bot.send_message(admin_id, text, reply_markup=keyboard)
                except Exception as e:
                    logger.error(f"Failed to send notification to {admin_id}: {e}")

    async def _on_login_200(self, data: dict):
        """Успешный вход"""
        ip = data["ip"]
        panel = data["panel"]

        self.db.log_login_attempt(ip, success=True, status_code=200, panel_name=panel)

        # Проверяем, не с нового ли IP
        geo = GeoIPLookup.lookup(ip)
        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))

        text = (
            f"✅ **Successful Login**\n\n"
            f"🌐 IP: `{ip}` {flag}\n"
            f"🌍 Country: {geo['country']}\n"
            f"🖥️ Panel: {panel}\n"
        )

        for admin_id in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(admin_id, text)
            except:
                pass

    async def _auto_ban_ip(self, ip: str, panel: str):
        """Автоматический бан IP"""
        from utils import IptablesManager

        if Config.DRY_RUN:
            logger.info(f"[DRY RUN] Would ban {ip}")
            return

        IptablesManager.ban_ip(ip)
        self.db.ban_ip(ip, reason=f"Autoban: {self.db.get_recent_attempts(ip, 5)} attempts", banned_by="autoban")
        IptablesManager.save_rules()

        logger.info(f"[AUTOBAN] Banned {ip}")

        if Config.NOTIFY_ON_BAN:
            text = f"🚫 **AUTOBAN**: `{ip}` заблокирован автоматически"
            for admin_id in Config.ADMIN_USER_IDS:
                try:
                    await self.bot.send_message(admin_id, text)
                except:
                    pass

        # Сбрасываем pending
        if ip in self._pending_bans:
            del self._pending_bans[ip]

    async def _on_high_cpu(self, data: dict):
        """Высокая нагрузка CPU"""
        text = (
            f"⚠️ **High CPU Usage**\n\n"
            f"🔴 CPU: **{data['cpu']}%**\n"
            f"📊 Threshold: {data['threshold']}%\n"
        )
        for admin_id in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(admin_id, text)
            except:
                pass

    async def _on_high_ram(self, data: dict):
        """Высокая нагрузка RAM"""
        text = (
            f"⚠️ **High RAM Usage**\n\n"
            f"🔴 RAM: **{data['ram']}%**\n"
            f"📊 Threshold: {data['threshold']}%\n"
        )
        for admin_id in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(admin_id, text)
            except:
                pass

    async def _on_high_connections(self, data: dict):
        """Много соединений"""
        text = (
            f"⚠️ **High Connections Count**\n\n"
            f"🔌 Connections: **{data['connections']}**\n"
            f"📊 Threshold: {data['threshold']}\n"
            f"🚨 Possible DDoS attack!\n"
        )
        for admin_id in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(admin_id, text)
            except:
                pass

    async def _on_container_down(self, data: dict):
        """Контейнер упал"""
        text = (
            f"🔴 **Container Down!**\n\n"
            f"🐳 Container: `{data['name']}`\n"
            f"⚠️ Status: STOPPED\n"
            f"🕐 Time: {data['timestamp']}\n"
        )
        for admin_id in Config.ADMIN_USER_IDS:
            try:
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔄 Restart", callback_data=f"docker_restart:{data['name']}")]
                ])
                await self.bot.send_message(admin_id, text, reply_markup=keyboard)
            except:
                pass

    async def _on_container_restart(self, data: dict):
        """Контейнер перезапустился"""
        text = (
            f"🔄 **Container Restarted**\n\n"
            f"🐳 Container: `{data['name']}`\n"
            f"✅ Status: RUNNING\n"
        )
        for admin_id in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(admin_id, text)
            except:
                pass

    def setup_handlers(self):
        """Настройка хендлеров команд"""

        # Команды
        self.dp.message.register(self.admin_handler.cmd_start, Command("start"))
        self.dp.message.register(self.admin_handler.cmd_status, Command("status"))
        self.dp.message.register(self.admin_handler.cmd_help, Command("help"))
        self.dp.message.register(self.admin_handler.cmd_banned, Command("banned"))
        self.dp.message.register(self.admin_handler.cmd_unban, Command("unban"))
        self.dp.message.register(self.admin_handler.cmd_connections, Command("connections"))
        self.dp.message.register(self.admin_handler.cmd_logs, Command("logs"))
        self.dp.message.register(self.admin_handler.cmd_backup, Command("backup"))
        self.dp.message.register(self.users_handler.cmd_users, Command("users"))

        # Callback queries — ловим ВСЕ callback
        from aiogram.types import CallbackQuery
        self.dp.callback_query.register(self.security_handler.handle_callback)

    async def periodic_tasks(self):
        """Периодические задачи"""
        while True:
            try:
                # Сохраняем метрики
                metrics = self.sys_monitor.get_full_status()
                self.db.save_metrics(
                    metrics["cpu"],
                    metrics["ram"]["percent"],
                    metrics["disk"]["percent"],
                    metrics["connections"],
                    metrics["network"]["bytes_recv"],
                    metrics["network"]["bytes_sent"],
                )

                # Очистка старых данных
                self.db.cleanup_old_data()

            except Exception as e:
                logger.error(f"Periodic task error: {e}")

            await asyncio.sleep(Config.SYSTEM_CHECK_INTERVAL)

    async def run(self):
        """Запуск бота"""
        print("=" * 60)
        print("🛡️  Marzban Security Bot v3")
        print("=" * 60)
        print(f"📋 Panels: {', '.join([p['name'] for p in PANELS])}")
        print(f"👥 Admins: {len(Config.ADMIN_USER_IDS)}")
        print(f"🔒 Autoban: {'ON' if Config.AUTOBAN_ENABLED else 'OFF'}")
        print("=" * 60)

        # Настройка
        self.setup_callbacks()
        self.setup_handlers()

        # Запуск мониторов
        self.sys_monitor.start()
        self.docker_monitor.start()
        self.log_monitor.start_all()

        # Запуск периодических задач
        asyncio.create_task(self.periodic_tasks())

        # Запуск бота
        logger.info("Starting bot...")
        await self.dp.start_polling(self.bot)


async def main():
    bot = MarzbanBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
