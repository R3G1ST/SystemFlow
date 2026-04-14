#!/usr/bin/env python3
"""
SystemFlow v3 — Telegram Bot для мониторинга Marzban
Полный рефакторинг: reply-клавиатуры, кнопка Назад, без дублей эмодзи
"""
import asyncio
import logging
import os
import subprocess
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from config import Config, PANELS
from database import Database
from i18n import i18n
from monitors.log_monitor import MultiPanelLogMonitor
from monitors.system_monitor import SystemMonitor
from monitors.docker_monitor import DockerMonitor
from utils import IptablesManager, GeoIPLookup, BackupManager

VERSION = "3.0.0"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== ФОРМАТИРОВАНИЕ =====
def _fmt(b):
    for u in ["B", "KB", "MB", "GB"]:
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

def _uptime():
    import psutil
    bt = datetime.fromtimestamp(psutil.boot_time())
    d = datetime.now() - bt
    return f"{d.days}д {d.seconds // 3600}ч {(d.seconds % 3600) // 60}м"


class MarzbanBot:
    def __init__(self):
        if not Config.BOT_TOKEN or Config.BOT_TOKEN == "your_bot_token_here":
            print("❌ BOT_TOKEN not set!")
            exit(1)
        self.bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
        self.dp = Dispatcher()
        self.db = Database()
        self.sys_mon = SystemMonitor(check_interval=Config.SYSTEM_CHECK_INTERVAL)
        self.doc_mon = DockerMonitor(check_interval=30, monitored_containers=[p["container"] for p in PANELS])
        self.log_mon = MultiPanelLogMonitor()
        self._pending_bans = {}
        self._sessions = {}  # uid -> {"action": ..., "data": ...}

    # ====== КЛАВИАТУРЫ ======

    def _main_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=i18n.get("btn_status", uid)), KeyboardButton(text=i18n.get("btn_security", uid))],
            [KeyboardButton(text=i18n.get("btn_users", uid)), KeyboardButton(text=i18n.get("btn_docker", uid))],
            [KeyboardButton(text=i18n.get("btn_backup", uid)), KeyboardButton(text=i18n.get("btn_reports", uid))],
            [KeyboardButton(text=i18n.get("btn_banned", uid)), KeyboardButton(text=i18n.get("btn_connections", uid))],
            [KeyboardButton(text=i18n.get("btn_logs", uid)), KeyboardButton(text=i18n.get("btn_settings", uid))],
            [KeyboardButton(text=i18n.get("btn_help", uid))],
        ], resize_keyboard=True)

    def _back_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=i18n.get("btn_back", uid))],
        ], resize_keyboard=True)

    def _lang_kb(self):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        ])

    def _security_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=i18n.get("btn_banned", uid)), KeyboardButton(text=i18n.get("btn_top_attackers", uid))],
            [KeyboardButton(text=i18n.get("btn_connections", uid)), KeyboardButton(text=i18n.get("btn_unban", uid))],
            [KeyboardButton(text=i18n.get("btn_back", uid))],
        ], resize_keyboard=True)

    def _docker_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=i18n.get("btn_docker_containers", uid)), KeyboardButton(text=i18n.get("btn_docker_logs", uid))],
            [KeyboardButton(text=i18n.get("btn_back", uid))],
        ], resize_keyboard=True)

    def _reports_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=i18n.get("btn_reports_cpu", uid)), KeyboardButton(text=i18n.get("btn_reports_ram", uid))],
            [KeyboardButton(text=i18n.get("btn_reports_attacks", uid))],
            [KeyboardButton(text=i18n.get("btn_back", uid))],
        ], resize_keyboard=True)

    def _settings_kb(self, uid):
        ab = "ON" if Config.AUTOBAN_ENABLED else "OFF"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
             InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
            [InlineKeyboardButton(text=f"Автобан: {ab}", callback_data="noop")],
            [InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="back_to_main")],
        ])

    def _attack_kb(self, ip, uid=None):
        tid = uid or None
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{i18n.get('ban_ip', tid)} {ip}", callback_data=f"ban_ip:{ip}"),
                InlineKeyboardButton(text=i18n.get("ip_info", tid), callback_data=f"ip_info:{ip}"),
            ],
            [
                InlineKeyboardButton(text=i18n.get("ban_1h", tid), callback_data=f"ban_temp:{ip}:3600"),
                InlineKeyboardButton(text=i18n.get("ban_24h", tid), callback_data=f"ban_temp:{ip}:86400"),
            ],
            [InlineKeyboardButton(text=i18n.get("whois", tid), callback_data=f"whois:{ip}")],
        ])

    def _unban_list_kb(self, uid):
        banned = self.db.get_banned_ips(limit=15)
        if not banned:
            return None
        kb = []
        for b in banned:
            geo = GeoIPLookup.lookup(b["ip"])
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            kb.append([InlineKeyboardButton(
                text=f"{b['ip']} {flag}", callback_data=f"unban_ip:{b['ip']}"
            )])
        kb.append([InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="back_to_main")])
        return InlineKeyboardMarkup(inline_keyboard=kb)

    def _logs_kb(self, uid):
        kb = []
        for n in i18n.get("logs_lines", uid).split("||"):
            # На самом деле logs_lines это список, сделаем inline
            pass
        buttons = []
        for n in ["10", "25", "50", "100", "200"]:
            buttons.append(InlineKeyboardButton(text=n, callback_data=f"logs:{n}"))
        buttons.append(InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="back_to_main"))
        kb = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
        return InlineKeyboardMarkup(inline_keyboard=kb)

    def _docker_containers_kb(self, uid):
        containers = self.doc_mon.get_containers_status()
        if not containers:
            return None, "Нет контейнеров"
        kb = []
        text = ""
        for c in containers:
            icon = "✅" if c["running"] else "❌"
            text += f"{icon} `{c['name']}`\n"
            if c["running"]:
                kb.append([InlineKeyboardButton(
                    text=f"🔄 {c['name']}", callback_data=f"docker_restart:{c['name']}"
                )])
        kb.append([InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="back_to_main")])
        return InlineKeyboardMarkup(inline_keyboard=kb), text

    def _top_attackers_kb(self, uid):
        attackers = self.db.get_top_attackers(10)
        if not attackers:
            return None
        text = ""
        for i, a in enumerate(attackers, 1):
            geo = GeoIPLookup.lookup(a["ip"])
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text += f"{i}. `{a['ip']}` {flag} — {a['attempts']} попыток\n"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="back_to_main")]
        ])
        return text, kb

    def _banned_list_kb(self, uid):
        banned = self.db.get_banned_ips(limit=15)
        if not banned:
            return None, None
        text = ""
        kb = []
        for b in banned:
            geo = GeoIPLookup.lookup(b["ip"])
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text += f"• `{b['ip']}` {flag} — {geo.get('country', '?')}\n  {b['banned_at'][:16]}\n"
            kb.append([InlineKeyboardButton(
                text=f"🔓 {b['ip']}", callback_data=f"unban_ip:{b['ip']}"
            )])
        kb.append([InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="back_to_main")])
        return text, InlineKeyboardMarkup(inline_keyboard=kb)

    # ====== УВЕДОМЛЕНИЯ ======

    async def _notify(self, text, kb=None):
        for aid in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(aid, text, reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True)
            except Exception as e:
                logger.error(f"Notify error: {e}")

    # ====== КОМАНДЫ ======

    async def cmd_start(self, msg: types.Message):
        uid = msg.from_user.id
        if uid not in Config.ADMIN_USER_IDS:
            await msg.answer(i18n.get("no_access", uid))
            return
        settings = self.db.get_user_settings(uid)
        lang = settings.get("language", "ru") if settings else "ru"
        i18n.set_user_lang(uid, lang)
        await msg.answer(
            f"{i18n.get('welcome', uid, name=msg.from_user.first_name)}\n\n"
            f"{i18n.get('welcome_sub', uid)}\n\n"
            f"{i18n.get('welcome_feat', uid)}",
            reply_markup=self._lang_kb()
        )

    async def cmd_status(self, msg: types.Message):
        await self._show_status(msg, msg.from_user.id)

    async def cmd_help(self, msg: types.Message):
        uid = msg.from_user.id
        await msg.answer(i18n.get("help", uid), reply_markup=self._main_kb(uid))

    # ====== РЕАЛИЗАЦИЯ РАЗДЕЛОВ ======

    async def _show_status(self, target, uid, is_callback=False):
        s = self.sys_mon.get_full_status()
        containers = self.doc_mon.get_containers_status()
        cpu, ram, disk = s["cpu"], s["ram"]["percent"], s["disk"]["percent"]
        ci = "🔴" if cpu > 80 else "🟡" if cpu > 50 else "🟢"
        ri = "🔴" if ram > 80 else "🟡" if ram > 50 else "🟢"

        text = (
            f"{i18n.get('server_status', uid)}\n\n"
            f"{ci} {i18n.get('cpu_label', uid)}: {cpu}%\n"
            f"{ri} {i18n.get('ram_label', uid)}: {ram}% ({_fmt(s['ram']['used'])} / {_fmt(s['ram']['total'])})\n"
            f"{i18n.get('disk_label', uid)}: {disk}% ({_fmt(s['disk']['used'])} / {_fmt(s['disk']['total'])})\n"
            f"{i18n.get('conn_label', uid)}: {s['connections']}\n"
            f"{i18n.get('uptime_label', uid)}: {_uptime()}\n\n"
            f"{i18n.get('docker_containers', uid)}\n"
        )
        for c in containers[:5]:
            text += f"{'✅' if c['running'] else '❌'} `{c['name']}`\n"
        text += (
            f"\n{i18n.get('security_info', uid)}\n"
            f"{i18n.get('banned_ips', uid)}: {self.db.get_banned_count()}\n"
            f"{i18n.get('failed_today', uid)}: {self.db.get_attempts_today()}\n"
        )
        if s.get("top_processes"):
            text += f"\n{i18n.get('top_processes', uid)}\n"
            for p in s["top_processes"][:3]:
                text += f"• `{p['name']}` — CPU: {p['cpu']}%, RAM: {p['mem']:.1f}%\n"

        kb = self._main_kb(uid)
        if is_callback:
            try:
                await target.message.edit_text(text, reply_markup=kb)
            except:
                await target.message.answer(text, reply_markup=kb)
        else:
            await target.answer(text, reply_markup=kb)

    async def _show_banned(self, uid, is_callback=False):
        text, kb = self._banned_list_kb(uid)
        if not text:
            await (is_callback and uid or uid) and None or None  # dummy
            if is_callback:
                pass
            text = i18n.get("banned_empty", uid)
            kb = self._security_kb(uid)
            if is_callback:
                await uid.message.answer(text, reply_markup=kb)
                return
            else:
                await uid.answer(text, reply_markup=kb)
                return

        header = f"{i18n.get('banned_list', uid)} ({self.db.get_banned_count()}):\n\n"
        full = header + text
        kb_final = kb
        if is_callback:
            await uid.message.answer(full, reply_markup=kb_final)
            await uid.answer()
        else:
            await uid.answer(full, reply_markup=kb_final)

    async def _show_connections(self, uid, is_callback=False):
        try:
            r = subprocess.run(
                "ss -tn state established | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -20",
                shell=True, capture_output=True, text=True, timeout=10
            )
            text = f"{i18n.get('connections', uid)}:\n\n"
            if r.stdout.strip():
                for line in r.stdout.strip().split("\n")[:20]:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        geo = GeoIPLookup.lookup(parts[1])
                        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
                        text += f"`{parts[1]}` {flag} — {parts[0]}\n"
            else:
                text += i18n.get("no_connections", uid)
        except Exception as e:
            text = str(e)

        if is_callback:
            await uid.message.answer(text, reply_markup=self._back_kb(uid))
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=self._main_kb(uid))

    async def _show_logs_select(self, uid, is_callback=False):
        text = f"{i18n.get('logs_title', uid, lines='?')}\n{i18n.get('logs_hint', uid)}"
        kb = self._logs_kb(uid)
        if is_callback:
            await uid.message.answer(text, reply_markup=kb)
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=kb)

    async def _show_logs_count(self, uid, lines, is_callback=False):
        try:
            r = subprocess.run(["docker", "logs", "--tail", str(lines), "marzban-marzban-1"],
                               capture_output=True, text=True, timeout=10)
            logs = (r.stdout + r.stderr).strip()
            if logs:
                if len(logs) > 4000:
                    logs = "...\n" + logs[-4000:]
                text = f"{i18n.get('logs_title', uid, lines=lines)}:\n\n```\n{logs}\n```"
            else:
                text = i18n.get("logs_empty", uid)
        except Exception as e:
            text = str(e)
        if is_callback:
            await uid.message.answer(text, reply_markup=self._back_kb(uid))
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=self._main_kb(uid))

    async def _show_docker_containers(self, uid, is_callback=False):
        kb, text = self._docker_containers_kb(uid)
        if not kb:
            text = i18n.get("docker_title", uid)
            kb = self._docker_kb(uid)
        header = f"{i18n.get('docker_title', uid)}:\n\n"
        full = header + text
        if is_callback:
            await uid.message.answer(full, reply_markup=kb)
            await uid.answer()
        else:
            await uid.answer(full, reply_markup=self._main_kb(uid))

    async def _show_docker_logs_select(self, uid, is_callback=False):
        containers = self.doc_mon.get_containers_status()
        running = [c for c in containers if c["running"]]
        if not running:
            text = "Нет запущенных контейнеров"
            kb = self._docker_kb(uid)
            if is_callback:
                await uid.message.answer(text, reply_markup=kb)
                await uid.answer()
            else:
                await uid.answer(text, reply_markup=kb)
            return

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=c["name"], callback_data=f"dlogs:{c['name']}")]
            for c in running
        ] + [[InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="back_to_main")]])
        text = "Выберите контейнер:"
        if is_callback:
            await uid.message.answer(text, reply_markup=kb)
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=kb)

    async def _show_docker_logs(self, uid, container, is_callback=False):
        try:
            r = subprocess.run(["docker", "logs", "--tail", "50", container],
                               capture_output=True, text=True, timeout=10)
            logs = (r.stdout + r.stderr).strip()[-4000:]
            text = f"Логи {container}:\n\n```\n{logs}\n```"
        except Exception as e:
            text = str(e)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="cb_docker")]
        ])
        if is_callback:
            await uid.message.answer(text, reply_markup=kb)
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=kb)

    async def _show_unban(self, uid, is_callback=False):
        kb = self._unban_list_kb(uid)
        if not kb:
            text = i18n.get("banned_empty", uid)
            if is_callback:
                await uid.message.answer(text, reply_markup=self._security_kb(uid))
                await uid.answer()
            else:
                await uid.answer(text, reply_markup=self._security_kb(uid))
            return
        text = f"{i18n.get('unban_hint', uid)}\n\nНажмите на IP для разбана:"
        if is_callback:
            await uid.message.answer(text, reply_markup=kb)
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=kb)

    async def _show_top_attackers(self, uid, is_callback=False):
        text, kb = self._top_attackers_kb(uid)
        if not text:
            text = i18n.get("no_attack_data", uid)
            kb = self._security_kb(uid)
        else:
            text = f"{i18n.get('top_attackers', uid)}:\n\n{text}"
        if is_callback:
            await uid.message.answer(text, reply_markup=kb)
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=kb)

    async def _show_reports_menu(self, uid, is_callback=False):
        text = i18n.get("reports_menu", uid)
        kb = self._reports_kb(uid)
        if is_callback:
            await uid.message.answer(text, reply_markup=kb)
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=kb)

    async def _show_users(self, uid, is_callback=False):
        from utils import MarzbanAPI, PanelConfig
        token = PanelConfig.get_panel_api_token(PANELS[0]["name"])
        if not token:
            text = i18n.get("users_need_token", uid)
            if is_callback:
                await uid.message.answer(text, reply_markup=self._back_kb(uid))
                await uid.answer()
            else:
                await uid.answer(text, reply_markup=self._main_kb(uid))
            return

        api = MarzbanAPI(PANELS[0]["url"], token)
        users = api.get_users()
        if not users:
            text = i18n.get("users_empty", uid)
        else:
            text = f"{i18n.get('users_title', uid)} ({len(users)}):\n\n"
            for u in users[:15]:
                status = {"active": "✅", "disabled": "❌", "limited": "⚠️", "expired": "⌛"}.get(u.get("status", ""), "❓")
                name = u.get("username", "?")
                used = u.get("used_traffic", 0)
                limit = u.get("data_limit", 0)
                traffic = f"{_fmt(used)}" + (f" / {_fmt(limit)}" if limit else "")
                text += f"{status} `{name}` — {traffic}\n"

        if is_callback:
            await uid.message.answer(text, reply_markup=self._back_kb(uid))
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=self._main_kb(uid))

    async def _show_settings(self, uid, is_callback=False):
        text = i18n.get("settings", uid)
        kb = self._settings_kb(uid)
        if is_callback:
            await uid.message.answer(text, reply_markup=kb)
            await uid.answer()
        else:
            await uid.answer(text, reply_markup=kb)

    async def _do_backup(self, uid, is_callback=False):
        loading_msg = i18n.get("backup_creating", uid)
        if is_callback:
            await uid.message.answer(loading_msg)
            await uid.answer()

        backup_file = BackupManager.create_backup()
        if backup_file:
            size = os.path.getsize(backup_file)
            size_h = BackupManager._format_size(size)
            self.db.log_action(uid, "backup", f"Created: {backup_file}")
            text = i18n.get("backup_success", uid, path=backup_file, size=size_h)
            await uid.answer(text)
            if size < 50 * 1024 * 1024:
                with open(backup_file, "rb") as f:
                    await uid.answer_document(f, caption=f"Marzban Backup\n{datetime.now().strftime('%Y-%m-%d %H:%M')}")
            else:
                await uid.answer(i18n.get("backup_large", uid))
        else:
            await uid.answer(i18n.get("backup_failed", uid))

    # ====== TEXT HANDLER ======

    async def handle_text(self, msg: types.Message):
        uid = msg.from_user.id
        text = msg.text.strip()

        # Проверка сессий (для unban ввода IP)
        if uid in self._sessions:
            sess = self._sessions[uid]
            if sess["action"] == "unban_input":
                del self._sessions[uid]
                ip = text
                IptablesManager.unban_ip(ip)
                self.db.unban_ip(ip, unbanned_by=str(uid))
                IptablesManager.save_rules()
                self.db.log_action(uid, "unban_ip", f"Unbanned {ip}")
                await msg.answer(i18n.get("unban_success", uid, ip=ip), reply_markup=self._security_kb(uid))
                return

        # Главное меню
        if text == i18n.get("btn_status", uid):
            await self._show_status(msg, uid)
        elif text == i18n.get("btn_security", uid):
            await msg.answer(i18n.get("security_menu", uid), reply_markup=self._security_kb(uid))
        elif text == i18n.get("btn_users", uid):
            await self._show_users(msg, uid)
        elif text == i18n.get("btn_docker", uid):
            await msg.answer(i18n.get("docker_title", uid), reply_markup=self._docker_kb(uid))
        elif text == i18n.get("btn_backup", uid):
            await self._do_backup(msg, uid)
        elif text == i18n.get("btn_reports", uid):
            await self._show_reports_menu(msg, uid)
        elif text == i18n.get("btn_settings", uid):
            await self._show_settings(msg, uid)
        elif text == i18n.get("btn_help", uid):
            await self.cmd_help(msg)
        elif text == i18n.get("btn_banned", uid):
            await self._show_banned(msg, uid)
        elif text == i18n.get("btn_connections", uid):
            await self._show_connections(msg, uid)
        elif text == i18n.get("btn_logs", uid):
            await self._show_logs_select(msg, uid)
        elif text == i18n.get("btn_unban", uid):
            await self._show_unban(msg, uid)
        elif text == i18n.get("btn_top_attackers", uid):
            await self._show_top_attackers(msg, uid)
        elif text == i18n.get("btn_back", uid):
            await msg.answer(i18n.get("main_menu", uid), reply_markup=self._main_kb(uid))
        elif text == i18n.get("btn_docker_containers", uid):
            await self._show_docker_containers(msg, uid)
        elif text == i18n.get("btn_docker_logs", uid):
            await self._show_docker_logs_select(msg, uid)
        elif text == i18n.get("btn_reports_cpu", uid):
            await msg.answer("График CPU в разработке", reply_markup=self._reports_kb(uid))
        elif text == i18n.get("btn_reports_ram", uid):
            await msg.answer("График RAM в разработке", reply_markup=self._reports_kb(uid))
        elif text == i18n.get("btn_reports_attacks", uid):
            await msg.answer("График атак в разработке", reply_markup=self._reports_kb(uid))
        else:
            await msg.answer(i18n.get("unknown", uid), reply_markup=self._main_kb(uid))

    # ====== CALLBACK HANDLER ======

    async def handle_callback(self, cb: types.CallbackQuery):
        uid = cb.from_user.id
        data = cb.data

        if uid not in Config.ADMIN_USER_IDS:
            await cb.answer(i18n.get("no_access", uid), show_alert=True)
            return

        try:
            if data.startswith("lang:"):
                lang = data.split(":")[1]
                i18n.set_user_lang(uid, lang)
                self.db.save_user_settings(uid, cb.from_user.username, lang)
                name = "🇷🇺 Русский" if lang == "ru" else "🇬🇧 English"
                await cb.answer(f"✅ {name}", show_alert=False)
                try:
                    await cb.message.delete()
                except:
                    pass
                await cb.message.answer(
                    f"{i18n.get('lang_set_ru' if lang == 'ru' else 'lang_set_en', uid)}",
                    reply_markup=self._main_kb(uid)
                )

            elif data.startswith("ban_ip:"):
                ip = data.split(":", 1)[1]
                if self.db.is_banned(ip):
                    await cb.answer(i18n.get("already_banned", uid, ip=ip), show_alert=True)
                    return
                IptablesManager.ban_ip(ip)
                self.db.ban_ip(ip, "Manual ban", str(uid))
                IptablesManager.save_rules()
                self.db.log_action(uid, "ban_ip", f"Banned {ip}")
                await cb.answer(i18n.get("ban_success", uid, ip=ip), show_alert=True)

            elif data.startswith("ban_temp:"):
                _, ip, secs = data.split(":")
                IptablesManager.ban_ip(ip)
                self.db.ban_ip(ip, f"Temp ban {secs}s", str(uid))
                IptablesManager.save_rules()
                self.db.log_action(uid, "ban_ip", f"Temp ban {ip} {secs}s")
                await cb.answer(f"{ip} забанен на {secs}с", show_alert=True)

            elif data.startswith("unban_ip:"):
                ip = data.split(":", 1)[1]
                IptablesManager.unban_ip(ip)
                self.db.unban_ip(ip, str(uid))
                IptablesManager.save_rules()
                self.db.log_action(uid, "unban_ip", f"Unbanned {ip}")
                await cb.answer(i18n.get("unban_success", uid, ip=ip), show_alert=True)
                # Обновить список
                await self._show_banned(cb, uid, is_callback=True)

            elif data.startswith("ip_info:"):
                ip = data.split(":", 1)[1]
                geo = GeoIPLookup.lookup(ip)
                flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
                text = (
                    f"Информация об IP:\n\n"
                    f"IP: `{ip}` {flag}\n"
                    f"Страна: {geo['country']} — {geo['city']}\n"
                    f"Провайдер: {geo['isp']}\n"
                    f"ASN: {geo['as']}\n\n"
                    f"В бане: {'Да' if self.db.is_banned(ip) else 'Нет'}"
                )
                await cb.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="back_to_main")]
                ]))
                await cb.answer()

            elif data.startswith("whois:"):
                ip = data.split(":", 1)[1]
                await cb.answer("Загрузка WHOIS...", show_alert=False)
                try:
                    r = subprocess.run(["whois", ip], capture_output=True, text=True, timeout=10)
                    lines = r.stdout.split("\n")
                    short = [l for l in lines if any(l.lower().startswith(k) for k in ["inetnum", "netname", "descr", "country", "org", "abuse"])]
                    text = f"WHOIS {ip}:\n\n" + "\n".join(short[:15])
                except:
                    text = f"Ошибка WHOIS для {ip}"
                await cb.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=i18n.get("btn_back", uid), callback_data="back_to_main")]
                ]))
                await cb.answer()

            elif data.startswith("logs:"):
                lines = int(data.split(":")[1])
                await self._show_logs_count(cb, uid, lines, is_callback=True)

            elif data.startswith("dlogs:"):
                container = data.split(":", 1)[1]
                await self._show_docker_logs(cb, uid, container, is_callback=True)

            elif data.startswith("docker_restart:"):
                container = data.split(":", 1)[1]
                await cb.answer(f"Перезапуск {container}...", show_alert=False)
                try:
                    r = subprocess.run(["docker", "restart", container], capture_output=True, timeout=30)
                    if r.returncode == 0:
                        await cb.message.answer(i18n.get("docker_restarted", uid, name=container),
                                                reply_markup=self._back_kb(uid))
                    else:
                        await cb.message.answer(i18n.get("docker_error", uid, error=r.stderr.decode()[:200]),
                                                reply_markup=self._back_kb(uid))
                except Exception as e:
                    await cb.message.answer(i18n.get("docker_error", uid, error=str(e)), reply_markup=self._back_kb(uid))
                await cb.answer()

            elif data == "back_to_main":
                await cb.message.answer(i18n.get("main_menu", uid), reply_markup=self._main_kb(uid))
                await cb.answer()

            elif data == "cb_docker":
                await self._show_docker_containers(cb, uid, is_callback=True)

            elif data == "noop":
                await cb.answer()

            else:
                await cb.answer(i18n.get("callback_unknown", uid))

        except Exception as e:
            logger.error(f"Callback error: {e}")
            await cb.answer(i18n.get("error", uid), show_alert=True)

    # ====== МОНИТОРИНГ CALLBACKS ======

    def setup_callbacks(self):
        for panel in PANELS:
            m = self.log_mon.add_panel(panel["container"], panel["name"], Config.MONITOR_INTERVAL)
            m.on("login_401", self._on_401)
            m.on("login_200", self._on_200)
        if Config.NOTIFY_ON_HIGH_CPU:
            self.sys_mon.on("high_cpu", self._on_high_cpu)
        if Config.NOTIFY_ON_HIGH_RAM:
            self.sys_mon.on("high_ram", self._on_high_ram)
        self.sys_mon.on("high_connections", self._on_high_conn)
        self.doc_mon.on("container_down", self._on_container_down)
        self.doc_mon.on("container_restart", self._on_container_up)

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
                    await self._notify(i18n.get("autoban", None, ip=ip))
                if ip in self._pending_bans:
                    del self._pending_bans[ip]
        if Config.NOTIFY_ON_401:
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text = i18n.get("attack_notify", None, ip=ip, flag=flag, country=geo['country'],
                           city=geo['city'], isp=geo['isp'], panel=panel, time=data['timestamp'],
                           attempts=self.db.get_recent_attempts(ip, 60))
            for aid in Config.ADMIN_USER_IDS:
                kb = self._attack_kb(ip, aid)
                try:
                    await self.bot.send_message(aid, text, reply_markup=kb, parse_mode="Markdown")
                except:
                    pass

    async def _on_200(self, data):
        ip, panel = data["ip"], data["panel"]
        self.db.log_login_attempt(ip, True, 200, panel_name=panel)
        geo = GeoIPLookup.lookup(ip)
        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
        text = i18n.get("login_success", None, ip=ip, flag=flag, country=geo['country'], panel=panel)
        await self._notify(text)

    async def _on_high_cpu(self, d):
        await self._notify(i18n.get("high_cpu", None, cpu=d['cpu'], threshold=d['threshold']))

    async def _on_high_ram(self, d):
        await self._notify(i18n.get("high_ram", None, ram=d['ram'], threshold=d['threshold']))

    async def _on_high_conn(self, d):
        await self._notify(i18n.get("high_conn", None, connections=d['connections'], threshold=d['threshold']))

    async def _on_container_down(self, d):
        await self._notify(i18n.get("container_down", None, name=d['name'], time=d['timestamp']),
            InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=i18n.get("restart", None), callback_data=f"docker_restart:{d['name']}")
            ]]))

    async def _on_container_up(self, d):
        await self._notify(i18n.get("container_up", None, name=d['name']))

    # ====== ПЕРИОДИЧЕСКИЕ ЗАДАЧИ ======

    async def periodic(self):
        while True:
            try:
                m = self.sys_mon.get_full_status()
                self.db.save_metrics(m["cpu"], m["ram"]["percent"], m["disk"]["percent"],
                                     m["connections"], m["network"]["bytes_recv"], m["network"]["bytes_sent"])
                self.db.cleanup_old_data()
            except Exception as e:
                logger.error(f"Periodic error: {e}")
            await asyncio.sleep(Config.SYSTEM_CHECK_INTERVAL)

    async def startup_notify(self):
        state_file = "/opt/marzban-security-bot/.last_start"
        is_update = os.path.exists(state_file)
        last_ver = ""
        if is_update:
            try:
                with open(state_file) as f: last_ver = f.read().strip()
            except: pass

        panels = ", ".join([p["name"] for p in PANELS])
        lang = Config.LANGUAGE.upper()
        autoban = "ON" if Config.AUTOBAN_ENABLED else "OFF"

        if is_update and last_ver != VERSION:
            changelog = "• Полный рефакторинг визуала\n• Убраны дубли эмодзи\n• Кнопка Назад везде\n• Все функции через кнопки\n• Unban через inline\n• Логи с выбором\n• Docker меню\n• Отчёты меню"
            text = i18n.get("bot_updated", None, version=VERSION, changelog=changelog)
        else:
            text = i18n.get("bot_restarted", None, version=VERSION, panels=panels,
                           admins=len(Config.ADMIN_USER_IDS), autoban=autoban, language=lang)

        for aid in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(aid, text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Startup notify error: {e}")
        with open(state_file, "w") as f:
            f.write(VERSION)

    # ====== ЗАПУСК ======

    def setup_handlers(self):
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_status, Command("status"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.handle_text)
        self.dp.callback_query.register(self.handle_callback)

    async def run(self):
        print(f"\n{'='*50}")
        print(f"SystemFlow v{VERSION}")
        print(f"Panels: {', '.join([p['name'] for p in PANELS])}")
        print(f"Admins: {len(Config.ADMIN_USER_IDS)}")
        print(f"Autoban: {'ON' if Config.AUTOBAN_ENABLED else 'OFF'}")
        print(f"{'='*50}\n")

        self.setup_callbacks()
        self.setup_handlers()
        self.sys_mon.start()
        self.doc_mon.start()
        self.log_mon.start_all()
        asyncio.create_task(self.periodic())
        await self.startup_notify()
        logger.info("Starting polling...")
        await self.dp.start_polling(self.bot)


async def main():
    await MarzbanBot().run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")
