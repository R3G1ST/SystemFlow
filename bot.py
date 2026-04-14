#!/usr/bin/env python3
"""
SystemFlow v3 — Telegram Bot для мониторинга Marzban
С reply-клавиатурами и полной локализацией RU/EN
"""
import asyncio
import logging
import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config, PANELS
from database import Database
from i18n import i18n
from monitors.log_monitor import MultiPanelLogMonitor
from monitors.system_monitor import SystemMonitor
from monitors.docker_monitor import DockerMonitor
from utils import IptablesManager, GeoIPLookup, BackupManager

VERSION = "3.0.0"
LAST_UPDATE = "2026-04-14"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MarzbanBot:
    def __init__(self):
        if not Config.BOT_TOKEN or Config.BOT_TOKEN == "your_bot_token_here":
            print("❌ BOT_TOKEN not set in .env!")
            exit(1)

        self.bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
        self.dp = Dispatcher()
        self.db = Database()
        self.sys_monitor = SystemMonitor(check_interval=Config.SYSTEM_CHECK_INTERVAL)
        self.docker_monitor = DockerMonitor(check_interval=30, monitored_containers=[p["container"] for p in PANELS])
        self.log_monitor = MultiPanelLogMonitor()
        self._pending_bans = {}

    # ===== КЛАВИАТУРЫ =====

    def _get_main_kb(self, telegram_id: int) -> ReplyKeyboardMarkup:
        """Reply клавиатура — главное меню"""
        buttons = [
            [KeyboardButton(text=i18n.get("btn_status", telegram_id)),
             KeyboardButton(text=i18n.get("btn_security", telegram_id))],
            [KeyboardButton(text=i18n.get("btn_users", telegram_id)),
             KeyboardButton(text=i18n.get("btn_docker", telegram_id))],
            [KeyboardButton(text=i18n.get("btn_backup", telegram_id)),
             KeyboardButton(text=i18n.get("btn_reports", telegram_id))],
            [KeyboardButton(text=i18n.get("btn_banned", telegram_id)),
             KeyboardButton(text=i18n.get("btn_connections", telegram_id))],
            [KeyboardButton(text=i18n.get("btn_logs", telegram_id)),
             KeyboardButton(text=i18n.get("btn_settings", telegram_id))],
            [KeyboardButton(text=i18n.get("btn_help", telegram_id))],
        ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, input_field_placeholder="Выберите действие...")

    def _get_lang_kb(self) -> InlineKeyboardMarkup:
        """Inline клавиатура выбора языка"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        ])

    def _get_security_kb(self, uid: int) -> ReplyKeyboardMarkup:
        """Reply клавиатура — безопасность"""
        buttons = [
            [KeyboardButton(text=i18n.get("btn_banned", uid)),
             KeyboardButton(text=i18n.get("btn_connections", uid))],
            [KeyboardButton(text=i18n.get("btn_logs", uid)),
             KeyboardButton(text="🔍 Top Attackers")],
            [KeyboardButton(text="↩️ " + i18n.get("btn_status", uid))],
        ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    def _get_docker_kb(self, uid: int) -> ReplyKeyboardMarkup:
        """Reply клавиатура — docker"""
        buttons = [
            [KeyboardButton(text="📊 Containers"), KeyboardButton(text="📝 Logs")],
            [KeyboardButton(text="↩️ " + i18n.get("btn_status", uid))],
        ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    def _get_attack_action_kb(self, ip: str, uid: int = None) -> InlineKeyboardMarkup:
        """Inline кнопки для уведомлений об атаках"""
        tid = uid if uid else None  # если нет uid, используем дефолтный язык
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🚫 {i18n.get('btn_ban_ip', tid)} {ip}", callback_data=f"ban_ip:{ip}"),
                InlineKeyboardButton(text=f"🔍 {i18n.get('btn_ip_info', tid)}", callback_data=f"ip_info:{ip}"),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_ban_1h", tid), callback_data=f"ban_temp:{ip}:3600"),
                InlineKeyboardButton(text=i18n.get("btn_ban_24h", tid), callback_data=f"ban_temp:{ip}:86400"),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_whois", tid), callback_data=f"whois:{ip}"),
            ],
        ])

    # ===== ХЕНДЛЕРЫ КОМАНД =====

    async def cmd_start(self, message: types.Message):
        uid = message.from_user.id
        if uid not in Config.ADMIN_USER_IDS:
            await message.answer(i18n.get("no_access", uid))
            return

        settings = self.db.get_user_settings(uid)
        lang = settings.get("language", "ru") if settings else "ru"
        i18n.set_user_lang(uid, lang)

        text = (
            f"{i18n.get('welcome_title', uid, name=message.from_user.first_name)}\n\n"
            f"{i18n.get('welcome_subtitle', uid)}\n\n"
            f"{i18n.get('welcome_features', uid)}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=self._get_lang_kb())

    async def cmd_status(self, message: types.Message):
        await self._send_status(message, message.from_user.id)

    async def cmd_help(self, message: types.Message):
        uid = message.from_user.id
        text = f"{i18n.get('help_title', uid)}\n\n{i18n.get('help_text', uid)}"
        await message.answer(text, parse_mode="Markdown", reply_markup=self._get_main_kb(uid))

    async def cmd_banned(self, message: types.Message):
        uid = message.from_user.id
        banned = self.db.get_banned_ips(limit=20)
        total = self.db.get_banned_count()
        if not banned:
            await message.answer(i18n.get("banned_list_empty", uid))
            return
        text = f"🚫 **{i18n.get('banned_list_title', uid)}** ({total})\n\n"
        for i, b in enumerate(banned, 1):
            geo = GeoIPLookup.lookup(b["ip"])
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text += f"{i}. `{b['ip']}` {flag} — {geo.get('country', '?')}\n   📅 {b['banned_at']}\n\n"
        await message.answer(text, parse_mode="Markdown")

    async def cmd_unban(self, message: types.Message):
        uid = message.from_user.id
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(i18n.get("unban_command", uid), parse_mode="Markdown")
            return
        ip = parts[1]
        IptablesManager.unban_ip(ip)
        self.db.unban_ip(ip, unbanned_by=str(uid))
        IptablesManager.save_rules()
        self.db.log_action(uid, "unban_ip", f"Unbanned {ip}")
        await message.answer(i18n.get("unban_ip_success", uid, ip=ip), parse_mode="Markdown")

    async def cmd_connections(self, message: types.Message):
        uid = message.from_user.id
        import subprocess
        try:
            result = subprocess.run(
                "ss -tn state established | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -20",
                shell=True, capture_output=True, text=True, timeout=10
            )
            text = f"🔌 **{i18n.get('connections_title', uid)}**\n\n"
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n")[:20]:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        count, ip = parts[0], parts[1]
                        geo = GeoIPLookup.lookup(ip)
                        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
                        text += f"`{ip}` {flag} — **{count}**\n"
            else:
                text += "—"
            await message.answer(text, parse_mode="Markdown")
        except Exception as e:
            await message.answer(f"❌ {e}")

    async def cmd_logs(self, message: types.Message):
        uid = message.from_user.id
        parts = message.text.split()
        lines = min(int(parts[1]) if len(parts) > 1 else 50, 200)
        import subprocess
        try:
            result = subprocess.run(["docker", "logs", "--tail", str(lines), "marzban-marzban-1"],
                                    capture_output=True, text=True, timeout=10)
            logs = (result.stdout + result.stderr).strip()
            if logs:
                if len(logs) > 4000:
                    logs = "...\n" + logs[-4000:]
                await message.answer(f"📝 {i18n.get('logs_title', uid, lines=lines)}\n\n```\n{logs}\n```", parse_mode="Markdown")
            else:
                await message.answer(i18n.get("logs_empty", uid))
        except Exception as e:
            await message.answer(f"❌ {e}")

    async def cmd_backup(self, message: types.Message):
        uid = message.from_user.id
        await message.answer(i18n.get("backup_creating", uid))
        backup_file = BackupManager.create_backup()
        if backup_file:
            size = os.path.getsize(backup_file)
            size_h = BackupManager._format_size(size)
            self.db.log_action(uid, "backup", f"Created: {backup_file}")
            await message.answer(i18n.get("backup_success", uid, path=backup_file, size=size_h), parse_mode="Markdown")
            if size < 50 * 1024 * 1024:
                with open(backup_file, "rb") as f:
                    await message.answer_document(f, caption=f"📦 Marzban Backup\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            else:
                await message.answer(i18n.get("backup_too_large", uid))
        else:
            await message.answer(i18n.get("backup_failed", uid))

    # ===== ОБРАБОТКА TEXT СООБЩЕНИЙ (reply кнопки) =====

    async def handle_text(self, message: types.Message):
        uid = message.from_user.id
        text = message.text.strip()

        # Маршрутизация по тексту reply-кнопок
        if text == i18n.get("btn_status"):
            await self.cmd_status(message)
        elif text == i18n.get("btn_security"):
            await message.answer(f"🔒 {i18n.get('security_menu_title', uid)}", parse_mode="Markdown",
                                 reply_markup=self._get_security_kb(uid))
        elif text == i18n.get("btn_banned"):
            await self.cmd_banned(message)
        elif text == i18n.get("btn_connections"):
            await self.cmd_connections(message)
        elif text == i18n.get("btn_logs"):
            await message.answer("📝 Отправьте `/logs 50`", parse_mode="Markdown")
        elif text == i18n.get("btn_users"):
            await message.answer("👥 Команда `/users` (нужен API токен)", parse_mode="Markdown")
        elif text == i18n.get("btn_docker"):
            await message.answer(f"🐳 {i18n.get('cmd_docker_title', uid)}", parse_mode="Markdown",
                                 reply_markup=self._get_docker_kb(uid))
        elif text == i18n.get("btn_backup"):
            await self.cmd_backup(message)
        elif text == i18n.get("btn_reports"):
            await message.answer("📈 Отчёты в разработке", parse_mode="Markdown")
        elif text == i18n.get("btn_settings"):
            await self._show_settings(message)
        elif text == i18n.get("btn_help"):
            await self.cmd_help(message)
        else:
            await message.answer(i18n.get("unknown_command", uid), reply_markup=self._get_main_kb(uid))

    async def _show_settings(self, message: types.Message):
        uid = message.from_user.id
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
             InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
            [InlineKeyboardButton(text=f"🚫 Автобан: {'ON' if Config.AUTOBAN_ENABLED else 'OFF'}", callback_data="noop")],
        ])
        await message.answer(f"⚙️ {i18n.get('settings_title', uid)}", reply_markup=kb)

    # ===== CALLBACK HANDLER =====

    async def handle_callback(self, callback: types.CallbackQuery):
        uid = callback.from_user.id
        data = callback.data

        if uid not in Config.ADMIN_USER_IDS:
            await callback.answer(i18n.get("no_access", uid), show_alert=True)
            return

        try:
            if data.startswith("lang:"):
                lang = data.split(":")[1]
                i18n.set_user_lang(uid, lang)
                self.db.save_user_settings(uid, callback.from_user.username, lang)
                await callback.answer(i18n.get("language_set", uid))
                # Удаляем inline клавиатуру языка и отправляем главное меню с reply
                await callback.message.edit_text(
                    i18n.get("language_set", uid),
                    reply_markup=types.ReplyKeyboardRemove()
                )
                await callback.message.answer(
                    f"✅ {i18n.get('main_menu', uid)}",
                    reply_markup=self._get_main_kb(uid),
                    parse_mode="Markdown"
                )

            elif data.startswith("ban_ip:"):
                ip = data.split(":", 1)[1]
                await self._ban_ip(callback, ip, uid, "permanent")

            elif data.startswith("ban_temp:"):
                parts = data.split(":")
                ip, secs = parts[1], parts[2]
                await self._ban_ip(callback, ip, uid, f"temporary_{secs}s")

            elif data.startswith("ip_info:"):
                ip = data.split(":", 1)[1]
                await self._show_ip_info(callback, ip)

            elif data.startswith("whois:"):
                ip = data.split(":", 1)[1]
                await self._show_whois(callback, ip)

            elif data == "noop":
                await callback.answer()

            else:
                await callback.answer(f"❓ {data[:30]}")

        except Exception as e:
            logger.error(f"Callback error: {e}")
            await callback.answer(i18n.get("error", uid), show_alert=True)

    async def _ban_ip(self, callback, ip, uid, ban_type):
        if self.db.is_banned(ip):
            await callback.answer(i18n.get("ip_already_banned", uid, ip=ip), show_alert=True)
            return
        if IptablesManager.ban_ip(ip):
            self.db.ban_ip(ip, reason="Manual ban via bot", banned_by=str(uid))
            IptablesManager.save_rules()
            self.db.log_action(uid, "ban_ip", f"Banned {ip} ({ban_type})")
            await callback.answer(i18n.get("ban_ip_success", uid, ip=ip), show_alert=True)
        else:
            await callback.answer(i18n.get("error", uid), show_alert=True)

    async def _show_ip_info(self, callback, ip):
        geo = GeoIPLookup.lookup(ip)
        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
        uid = callback.from_user.id
        text = (
            f"🔍 **IP Information**\n\n"
            f"🌐 IP: `{ip}` {flag}\n"
            f"🌍 {geo['country']} — {geo['city']}\n"
            f"🏢 {geo['isp']}\n"
            f"🔌 {geo['as']}\n\n"
            f"🚫 Banned: **{'Да' if self.db.is_banned(ip) else 'Нет'}**"
        )
        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()

    async def _show_whois(self, callback, ip):
        import subprocess
        await callback.answer("⏳ WHOIS...", show_alert=False)
        try:
            result = subprocess.run(["whois", ip], capture_output=True, text=True, timeout=10)
            lines = result.stdout.split("\n")
            short = [l for l in lines if any(l.lower().startswith(k) for k in ["inetnum", "netname", "descr", "country", "org", "abuse"])]
            text = f"🌐 **WHOIS {ip}**\n\n" + "\n".join(short[:15])
        except:
            text = f"❌ WHOIS error for {ip}"
        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()

    # ===== МОНИТОРИНГ CALLBACKS =====

    def setup_callbacks(self):
        for panel in PANELS:
            mon = self.log_monitor.add_panel(panel["container"], panel["name"], Config.MONITOR_INTERVAL)
            mon.on("login_401", self._on_401)
            mon.on("login_200", self._on_200)
        if Config.NOTIFY_ON_HIGH_CPU:
            self.sys_monitor.on("high_cpu", self._on_high_cpu)
        if Config.NOTIFY_ON_HIGH_RAM:
            self.sys_monitor.on("high_ram", self._on_high_ram)
        self.sys_monitor.on("high_connections", self._on_high_conn)
        self.docker_monitor.on("container_down", self._on_container_down)
        self.docker_monitor.on("container_restart", self._on_container_up)

    async def _notify_all(self, text, kb=None):
        for aid in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(aid, text, reply_markup=kb, parse_mode="Markdown")
            except:
                pass

    async def _on_401(self, data):
        ip, panel = data["ip"], data["panel"]
        geo = GeoIPLookup.lookup(ip)
        self.db.log_login_attempt(ip, False, 401, panel_name=panel, country=geo.get("country"))
        if Config.AUTOBAN_ENABLED:
            attempts = self.db.get_recent_attempts(ip, Config.BAN_TIME_WINDOW // 60)
            if attempts >= Config.MAX_LOGIN_ATTEMPTS and ip not in self._pending_bans:
                self._pending_bans[ip] = True
                IptablesManager.ban_ip(ip)
                self.db.ban_ip(ip, f"Autoban: {attempts} attempts", "autoban")
                IptablesManager.save_rules()
                if Config.NOTIFY_ON_BAN:
                    await self._notify_all(f"🚫 **AUTOBAN**: `{ip}`")
                if ip in self._pending_bans:
                    del self._pending_bans[ip]
        if Config.NOTIFY_ON_401:
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text = i18n.get("attack_notification", None,
                           ip=ip, flag=flag, country=geo['country'], city=geo['city'],
                           isp=geo['isp'], panel=panel, time=data['timestamp'],
                           attempts=self.db.get_recent_attempts(ip, 60))
            for aid in Config.ADMIN_USER_IDS:
                kb = self._get_attack_action_kb(ip, aid)
                try:
                    await self.bot.send_message(aid, text, reply_markup=kb, parse_mode="Markdown")
                except:
                    pass

    async def _on_200(self, data):
        ip, panel = data["ip"], data["panel"]
        self.db.log_login_attempt(ip, True, 200, panel_name=panel)
        geo = GeoIPLookup.lookup(ip)
        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
        text = i18n.get("successful_login", None, ip=ip, flag=flag, country=geo['country'], panel=panel)
        await self._notify_all(text)

    async def _on_high_cpu(self, data):
        await self._notify_all(i18n.get("high_cpu_alert", None, cpu=data['cpu'], threshold=data['threshold']))

    async def _on_high_ram(self, data):
        await self._notify_all(i18n.get("high_ram_alert", None, ram=data['ram'], threshold=data['threshold']))

    async def _on_high_conn(self, data):
        await self._notify_all(i18n.get("high_connections_alert", None, connections=data['connections'], threshold=data['threshold']))

    async def _on_container_down(self, data):
        await self._notify_all(i18n.get("container_down", None, name=data['name'], time=data['timestamp']),
                               InlineKeyboardMarkup(inline_keyboard=[[
                                   InlineKeyboardButton(text=i18n.get("btn_restart_container"), callback_data=f"docker_restart:{data['name']}")
                               ]]))

    async def _on_container_up(self, data):
        await self._notify_all(i18n.get("container_restart", None, name=data['name']))

    # ===== STATUS =====

    async def _send_status(self, target, uid):
        s = self.sys_monitor.get_full_status()
        containers = self.docker_monitor.get_containers_status()
        cpu, ram, disk = s["cpu"], s["ram"]["percent"], s["disk"]["percent"]
        cpu_i = "🔴" if cpu > 80 else "🟡" if cpu > 50 else "🟢"
        ram_i = "🔴" if ram > 80 else "🟡" if ram > 50 else "🟢"
        text = (
            f"📊 **{i18n.get('server_status', uid)}**\n\n"
            f"{cpu_i} CPU: {cpu}%\n"
            f"{ram_i} RAM: {ram}% ({self._fmt(s['ram']['used'])} / {self._fmt(s['ram']['total'])})\n"
            f"💾 Disk: {s['disk']['percent']}% ({self._fmt(s['disk']['used'])} / {self._fmt(s['disk']['total'])})\n"
            f"🔌 {i18n.get('connections', uid)}: {s['connections']}\n"
            f"⏱️ {i18n.get('uptime', uid)}: {s['uptime']}\n\n"
            f"🐳 **{i18n.get('docker_containers', uid)}**\n"
        )
        for c in containers[:5]:
            text += f"{'✅' if c['running'] else '❌'} `{c['name']}`\n"
        text += f"\n🛡️ **{i18n.get('security_info', uid)}**\n"
        text += f"🚫 {i18n.get('banned_ips', uid)}: {self.db.get_banned_count()}\n"
        text += f"🔐 {i18n.get('failed_today', uid)}: {self.db.get_attempts_today()}\n"
        if s.get("top_processes"):
            text += f"\n🔝 **{i18n.get('top_processes', uid)}**\n"
            for p in s["top_processes"][:3]:
                text += f"• `{p['name']}` — CPU: {p['cpu']}%, RAM: {p['mem']:.1f}%\n"
        kb = self._get_main_kb(uid)
        await target.answer(text, parse_mode="Markdown", reply_markup=kb)

    @staticmethod
    def _fmt(b):
        for u in ["B", "KB", "MB", "GB"]:
            if b < 1024: return f"{b:.1f} {u}"
            b /= 1024
        return f"{b:.1f} TB"

    # ===== ЗАПУСК =====

    def setup_handlers(self):
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_status, Command("status"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_banned, Command("banned"))
        self.dp.message.register(self.cmd_unban, Command("unban"))
        self.dp.message.register(self.cmd_connections, Command("connections"))
        self.dp.message.register(self.cmd_logs, Command("logs"))
        self.dp.message.register(self.cmd_backup, Command("backup"))
        self.dp.message.register(self.handle_text)  # reply buttons — последний
        self.dp.callback_query.register(self.handle_callback)

    async def periodic(self):
        while True:
            try:
                m = self.sys_monitor.get_full_status()
                self.db.save_metrics(m["cpu"], m["ram"]["percent"], m["disk"]["percent"],
                                     m["connections"], m["network"]["bytes_recv"], m["network"]["bytes_sent"])
                self.db.cleanup_old_data()
            except Exception as e:
                logger.error(f"Periodic error: {e}")
            await asyncio.sleep(Config.SYSTEM_CHECK_INTERVAL)

    async def send_startup_notification(self):
        """Отправить уведомление о запуске бота"""
        # Проверяем, это первый запуск или перезапуск
        state_file = "/opt/marzban-security-bot/.last_start"
        is_update = os.path.exists(state_file)
        last_version = ""
        if is_update:
            try:
                with open(state_file) as f:
                    last_version = f.read().strip()
            except:
                pass

        panels = ", ".join([p["name"] for p in PANELS])
        lang = Config.LANGUAGE
        autoban = "ON" if Config.AUTOBAN_ENABLED else "OFF"

        if is_update and last_version != VERSION:
            # Это обновление
            changelog = "• Исправлены callback-кнопки\n• Добавлена reply-клавиатура\n• Полная локализация RU/EN\n• Уведомления о рестарте"
            text = i18n.get("bot_updated", None, version=VERSION, changelog=changelog)
        else:
            # Обычный рестарт
            text = i18n.get("bot_restarted", None, version=VERSION, panels=panels,
                           admins=len(Config.ADMIN_USER_IDS), autoban=autoban, language=lang.upper())

        for aid in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(aid, text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Startup notification error: {e}")

        # Сохраняем версию
        with open(state_file, "w") as f:
            f.write(VERSION)

    async def run(self):
        print(f"\n{'='*50}")
        print(f"🛡️  SystemFlow v{VERSION}")
        print(f"📋 Panels: {', '.join([p['name'] for p in PANELS])}")
        print(f"👥 Admins: {len(Config.ADMIN_USER_IDS)}")
        print(f"🔒 Autoban: {'ON' if Config.AUTOBAN_ENABLED else 'OFF'}")
        print(f"{'='*50}\n")

        self.setup_callbacks()
        self.setup_handlers()
        self.sys_monitor.start()
        self.docker_monitor.start()
        self.log_monitor.start_all()
        asyncio.create_task(self.periodic())

        # Уведомление о запуске
        await self.send_startup_notification()

        logger.info("Starting polling...")
        await self.dp.start_polling(self.bot)


async def main():
    bot = MarzbanBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")
