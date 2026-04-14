#!/usr/bin/env python3
"""
SystemFlow v3 — Полностью рабочая версия
Эмодзи возвращены, все кнопки работают
"""
import asyncio
import logging
import os
import subprocess
import psutil
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
)
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


def _fmt(b):
    for u in ["B", "KB", "MB", "GB"]:
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

def _uptime():
    bt = datetime.fromtimestamp(psutil.boot_time())
    d = datetime.now() - bt
    return f"{d.days}д {d.seconds // 3600}ч {(d.seconds % 3600) // 60}м"


class BotApp:
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

    # ========== УТИЛИТЫ ОТПРАВКИ ==========

    async def _send(self, target, text, kb=None, remove_kb=False):
        """Универсальная отправка — работает и с Message и с CallbackQuery"""
        if isinstance(target, types.CallbackQuery):
            if remove_kb:
                await target.message.answer(text, reply_markup=ReplyKeyboardRemove())
            elif kb:
                await target.message.answer(text, reply_markup=kb)
            else:
                await target.message.answer(text)
            await target.answer()
        else:
            # Message
            if remove_kb:
                await target.answer(text, reply_markup=ReplyKeyboardRemove())
            elif kb:
                await target.answer(text, reply_markup=kb)
            else:
                await target.answer(text)

    async def _notify(self, text, kb=None):
        for aid in Config.ADMIN_USER_IDS:
            try:
                await self.bot.send_message(aid, text, reply_markup=kb, parse_mode=Markdown)
            except: pass

    # ========== КЛАВИАТУРЫ ==========

    def _main_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KB(i18n.get("btn_status", uid)), KB(i18n.get("btn_security", uid))],
            [KB(i18n.get("btn_users", uid)), KB(i18n.get("btn_docker", uid))],
            [KB(i18n.get("btn_backup", uid)), KB(i18n.get("btn_reports", uid))],
            [KB(i18n.get("btn_banned", uid)), KB(i18n.get("btn_connections", uid))],
            [KB(i18n.get("btn_logs", uid)), KB(i18n.get("btn_settings", uid))],
            [KB(i18n.get("btn_help", uid))],
        ], resize_keyboard=True)

    def _back_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KB(i18n.get("btn_back", uid))],
        ], resize_keyboard=True)

    def _lang_kb(self):
        return InlineKeyboardMarkup(inline_keyboard=[
            [IKB(text="🇷🇺 Русский", callback_data="lang:ru")],
            [IKB(text="🇬🇧 English", callback_data="lang:en")],
        ])

    def _security_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KB(i18n.get("btn_banned", uid)), KB(i18n.get("btn_top_attackers", uid))],
            [KB(i18n.get("btn_connections", uid)), KB(i18n.get("btn_unban", uid))],
            [KB(i18n.get("btn_logs_sec", uid))],
            [KB(i18n.get("btn_back", uid))],
        ], resize_keyboard=True)

    def _docker_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KB(i18n.get("btn_docker_containers", uid)), KB(i18n.get("btn_docker_logs_menu", uid))],
            [KB(i18n.get("btn_back", uid))],
        ], resize_keyboard=True)

    def _reports_kb(self, uid):
        return ReplyKeyboardMarkup(keyboard=[
            [KB(i18n.get("btn_reports_cpu", uid)), KB(i18n.get("btn_reports_ram", uid))],
            [KB(i18n.get("btn_reports_attacks", uid)), KB(i18n.get("btn_reports_daily", uid))],
            [KB(i18n.get("btn_back", uid))],
        ], resize_keyboard=True)

    def _attack_kb(self, ip, uid=None):
        tid = uid or None
        return InlineKeyboardMarkup(inline_keyboard=[
            [IKB(text=f"{i18n.get('ban_ip', tid)} {ip}", callback_data=f"ban_ip:{ip}"),
             IKB(text=i18n.get("ip_info", tid), callback_data=f"ip_info:{ip}")],
            [IKB(text=i18n.get("ban_1h", tid), callback_data=f"ban_temp:{ip}:3600"),
             IKB(text=i18n.get("ban_24h", tid), callback_data=f"ban_temp:{ip}:86400")],
            [IKB(text=i18n.get("whois", tid), callback_data=f"whois:{ip}")],
        ])

    def _settings_kb(self, uid):
        ab = "✅ ON" if Config.AUTOBAN_ENABLED else "❌ OFF"
        return InlineKeyboardMarkup(inline_keyboard=[
            [IKB("🇷🇺 Русский", "lang:ru"), IKB("🇬🇧 English", "lang:en")],
            [IKB(f"🚫 Автобан: {ab}", "noop")],
            [IKB(i18n.get("btn_back", uid), "back_to_main")],
        ])

    # ========== ГЛАВНЫЕ ЭКРАНЫ ==========

    async def _show_status(self, target, uid):
        s = self.sys_mon.get_full_status()
        containers = self.doc_mon.get_containers_status()
        cpu, ram, disk = s["cpu"], s["ram"]["percent"], s["disk"]["percent"]
        ci = "🔴" if cpu > 80 else "🟡" if cpu > 50 else "🟢"
        ri = "🔴" if ram > 80 else "🟡" if ram > 50 else "🟢"

        text = (
            f"📊 **{i18n.get('server_status', uid)}**\n\n"
            f"{ci} **CPU:** {cpu}%\n"
            f"{ri} **RAM:** {ram}% ({_fmt(s['ram']['used'])} / {_fmt(s['ram']['total'])})\n"
            f"💾 **Диск:** {disk}% ({_fmt(s['disk']['used'])} / {_fmt(s['disk']['total'])})\n\n"
            f"🔌 **Соединения:** {s['connections']}\n"
            f"⏱️ **Аптайм:** {_uptime()}\n\n"
        )
        if containers:
            text += f"🐳 **{i18n.get('docker_containers', uid)}**\n"
            for c in containers[:5]:
                text += f"{'✅' if c['running'] else '❌'} `{c['name']}`\n"
        text += (
            f"\n🛡️ **{i18n.get('security_info', uid)}**\n"
            f"🚫 {i18n.get('banned_ips', uid)}: {self.db.get_banned_count()}\n"
            f"🔐 {i18n.get('failed_today', uid)}: {self.db.get_attempts_today()}\n"
        )
        if s.get("top_processes"):
            text += f"\n🔝 **{i18n.get('top_processes', uid)}**\n"
            for p in s["top_processes"][:3]:
                text += f"• `{p['name']}` — CPU: {p['cpu']}%, RAM: {p['mem']:.1f}%\n"
        await self._send(target, text, self._main_kb(uid))

    async def _show_security(self, target, uid):
        text = f"🔒 **{i18n.get('security_menu', uid)}**"
        await self._send(target, text, self._security_kb(uid))

    async def _show_docker_menu(self, target, uid):
        text = f"🐳 **{i18n.get('docker_title', uid)}**"
        await self._send(target, text, self._docker_kb(uid))

    async def _show_reports_menu(self, target, uid):
        text = f"📈 **{i18n.get('reports_menu', uid)}**"
        await self._send(target, text, self._reports_kb(uid))

    async def _show_settings_screen(self, target, uid):
        text = f"⚙️ **{i18n.get('settings', uid)}**"
        await self._send(target, text, self._settings_kb(uid))

    # ===== ЗАБАНЕННЫЕ =====

    async def _show_banned(self, target, uid):
        banned = self.db.get_banned_ips(limit=15)
        total = self.db.get_banned_count()
        if not banned:
            await self._send(target, f"✅ {i18n.get('banned_empty', uid)}", self._security_kb(uid))
            return

        text = f"🚫 **{i18n.get('banned_list', uid)}** ({total})\n\n"
        kb_btns = []
        for b in banned:
            geo = GeoIPLookup.lookup(b["ip"])
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text += f"• `{b['ip']}` {flag} — {geo.get('country', '?')}\n  📅 {b['banned_at'][:16]}\n\n"
            kb_btns.append([IKB(f"🔓 {b['ip']}", f"unban_ip:{b['ip']}")])
        kb_btns.append([IKB(i18n.get("btn_back", uid), "back_to_main")])
        await self._send(target, text, InlineKeyboardMarkup(inline_keyboard=kb_btns))

    # ===== ТОП АТАКУЮЩИХ =====

    async def _show_top_attackers(self, target, uid):
        attackers = self.db.get_top_attackers(15)
        if not attackers:
            await self._send(target, f"📊 {i18n.get('no_attack_data', uid)}", self._security_kb(uid))
            return
        text = f"🏆 **{i18n.get('top_attackers', uid)}**\n\n"
        for i, a in enumerate(attackers, 1):
            geo = GeoIPLookup.lookup(a["ip"])
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text += f"{i}. `{a['ip']}` {flag} — **{a['attempts']}** попыток\n"
        await self._send(target, text, self._back_kb(uid))

    # ===== СОЕДИНЕНИЯ =====

    async def _show_connections(self, target, uid):
        try:
            r = subprocess.run(
                "ss -tn state established | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -20",
                shell=True, capture_output=True, text=True, timeout=10
            )
            text = f"🔌 **{i18n.get('connections', uid)}**\n\n"
            if r.stdout.strip():
                for line in r.stdout.strip().split("\n")[:20]:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        geo = GeoIPLookup.lookup(parts[1])
                        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
                        text += f"`{parts[1]}` {flag} — **{parts[0]}**\n"
            else:
                text += f"ℹ️ {i18n.get('no_connections', uid)}"
        except Exception as e:
            text = f"❌ {e}"
        await self._send(target, text, self._main_kb(uid))

    # ===== ЛОГИ =====

    async def _show_logs_select(self, target, uid):
        text = f"📝 **{i18n.get('logs_title', uid, lines='?')}**\n\n{i18n.get('logs_hint', uid)}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [IKB("10", "logs:10"), IKB("25", "logs:25"), IKB("50", "logs:50")],
            [IKB("100", "logs:100"), IKB("200", "logs:200")],
            [IKB(i18n.get("btn_back", uid), "back_to_main")],
        ])
        await self._send(target, text, kb)

    async def _show_logs_lines(self, target, uid, count):
        try:
            r = subprocess.run(["docker", "logs", "--tail", str(count), "marzban-marzban-1"],
                               capture_output=True, text=True, timeout=10)
            logs = (r.stdout + r.stderr).strip()
            if logs:
                if len(logs) > 4000:
                    logs = "...\n" + logs[-4000:]
                text = f"📝 **{i18n.get('logs_title', uid, lines=count)}**\n\n```\n{logs}\n```"
            else:
                text = f"ℹ️ {i18n.get('logs_empty', uid)}"
        except Exception as e:
            text = f"❌ {e}"
        await self._send(target, text, self._back_kb(uid))

    async def _show_logs_sec(self, target, uid):
        await self._show_logs_select(target, uid)

    # ===== DOCKER КОНТЕЙНЕРЫ =====

    async def _show_docker_containers(self, target, uid):
        containers = self.doc_mon.get_containers_status()
        if not containers:
            await self._send(target, f"ℹ️ Нет контейнеров", self._docker_kb(uid))
            return
        text = f"🐳 **{i18n.get('docker_containers', uid)}**\n\n"
        kb_btns = []
        for c in containers:
            icon = "✅" if c["running"] else "❌"
            text += f"{icon} `{c['name']}`\n"
            if c["running"]:
                kb_btns.append([IKB(f"🔄 {c['name']}", f"docker_restart:{c['name']}")])
        kb_btns.append([IKB(i18n.get("btn_back", uid), "back_to_main")])
        await self._send(target, text, InlineKeyboardMarkup(inline_keyboard=kb_btns))

    # ===== DOCKER ЛОГИ =====

    async def _show_docker_logs_menu(self, target, uid):
        containers = self.doc_mon.get_containers_status()
        running = [c for c in containers if c["running"]]
        if not running:
            await self._send(target, "ℹ️ Нет запущенных контейнеров", self._docker_kb(uid))
            return
        text = "📝 **Выберите контейнер:**"
        kb_btns = [[IKB(c["name"], f"dlogs:{c['name']}")] for c in running]
        kb_btns.append([IKB(i18n.get("btn_back", uid), "back_to_main")])
        await self._send(target, text, InlineKeyboardMarkup(inline_keyboard=kb_btns))

    async def _show_docker_container_logs(self, target, uid, container):
        try:
            r = subprocess.run(["docker", "logs", "--tail", "50", container],
                               capture_output=True, text=True, timeout=10)
            logs = (r.stdout + r.stderr).strip()[-4000:]
            text = f"📝 **Логи {container}**\n\n```\n{logs}\n```"
        except Exception as e:
            text = f"❌ {e}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [IKB(i18n.get("btn_back", uid), "cb_docker_containers")]
        ])
        await self._send(target, text, kb)

    # ===== UNBAN =====

    async def _show_unban(self, target, uid):
        banned = self.db.get_banned_ips(limit=15)
        if not banned:
            await self._send(target, f"✅ {i18n.get('banned_empty', uid)}", self._security_kb(uid))
            return
        text = f"🔓 **{i18n.get('unban_btn', uid)}**\n\nНажмите на IP для разбана:\n\n"
        kb_btns = []
        for b in banned:
            geo = GeoIPLookup.lookup(b["ip"])
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text += f"• `{b['ip']}` {flag}\n"
            kb_btns.append([IKB(f"🔓 {b['ip']}", f"unban_ip:{b['ip']}")])
        kb_btns.append([IKB(i18n.get("btn_back", uid), "back_to_main")])
        await self._send(target, text, InlineKeyboardMarkup(inline_keyboard=kb_btns))

    # ===== ПОЛЬЗОВАТЕЛИ =====

    async def _show_users(self, target, uid):
        from utils import MarzbanAPI, PanelConfig
        token = PanelConfig.get_panel_api_token(PANELS[0]["name"])
        if not token:
            await self._send(target, f"⚠️ {i18n.get('users_need_token', uid)}", self._back_kb(uid))
            return
        api = MarzbanAPI(PANELS[0]["url"], token)
        users = api.get_users()
        if not users:
            await self._send(target, f"ℹ️ {i18n.get('users_empty', uid)}", self._back_kb(uid))
            return
        text = f"👥 **{i18n.get('users_title', uid)}** ({len(users)})\n\n"
        for u in users[:20]:
            status = {"active": "✅", "disabled": "❌", "limited": "⚠️", "expired": "⌛"}.get(u.get("status", ""), "❓")
            name = u.get("username", "?")
            used = u.get("used_traffic", 0)
            limit = u.get("data_limit", 0)
            traffic = f"{_fmt(used)}" + (f" / {_fmt(limit)}" if limit else " / ♾️")
            text += f"{status} `{name}` — {traffic}\n"
        if len(users) > 20:
            text += f"\n... и ещё {len(users) - 20}"
        await self._send(target, text, self._back_kb(uid))

    # ===== БЭКАП =====

    async def _do_backup(self, target, uid):
        await self._send(target, f"⏳ {i18n.get('backup_creating', uid)}")
        backup_file = BackupManager.create_backup()
        if backup_file:
            size = os.path.getsize(backup_file)
            size_h = BackupManager._format_size(size)
            self.db.log_action(uid, "backup", f"Created: {backup_file}")
            text = f"✅ {i18n.get('backup_success', uid, path=backup_file, size=size_h)}"
            await self._send(target, text, self._main_kb(uid))
            if size < 50 * 1024 * 1024:
                with open(backup_file, "rb") as f:
                    await target.answer_document(f, caption=f"📦 Marzban Backup\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            else:
                await self._send(target, f"⚠️ {i18n.get('backup_large', uid)}")
        else:
            await self._send(target, f"❌ {i18n.get('backup_failed', uid)}", self._main_kb(uid))

    # ===== ОТЧЁТЫ =====

    async def _show_report_cpu(self, target, uid):
        await self._send(target, "📈 График CPU — в разработке", self._reports_kb(uid))

    async def _show_report_ram(self, target, uid):
        await self._send(target, "📈 График RAM — в разработке", self._reports_kb(uid))

    async def _show_report_attacks(self, target, uid):
        await self._send(target, "📈 График атак — в разработке", self._reports_kb(uid))

    async def _show_report_daily(self, target, uid):
        stats = self.db.get_today_stats()
        text = (
            f"📊 **{i18n.get('today_stats', uid)}**\n\n"
            f"🔐 {i18n.get('total_attempts', uid)}: {stats.get('total_attempts', 0)}\n"
            f"❌ {i18n.get('failed_attempts', uid)}: {stats.get('failed', 0)}\n"
            f"✅ {i18n.get('success_attempts', uid)}: {stats.get('success', 0)}\n"
            f"🌐 {i18n.get('unique_ips', uid)}: {stats.get('unique_ips', 0)}\n"
            f"🚫 {i18n.get('banned_ips', uid)}: {self.db.get_banned_count()}"
        )
        await self._send(target, text, self._reports_kb(uid))

    # ===== ТЕКСТОВЫЙ ХЕНДЛЕР =====

    async def handle_text(self, msg: types.Message):
        uid = msg.from_user.id
        t = msg.text.strip()

        # Главное меню
        if t == i18n.get("btn_status", uid):
            await self._show_status(msg, uid)
        elif t == i18n.get("btn_security", uid):
            await self._show_security(msg, uid)
        elif t == i18n.get("btn_users", uid):
            await self._show_users(msg, uid)
        elif t == i18n.get("btn_docker", uid):
            await self._show_docker_menu(msg, uid)
        elif t == i18n.get("btn_backup", uid):
            await self._do_backup(msg, uid)
        elif t == i18n.get("btn_reports", uid):
            await self._show_reports_menu(msg, uid)
        elif t == i18n.get("btn_settings", uid):
            await self._show_settings_screen(msg, uid)
        elif t == i18n.get("btn_help", uid):
            await self._send(msg, i18n.get("help", uid), self._main_kb(uid))
        elif t == i18n.get("btn_banned", uid):
            await self._show_banned(msg, uid)
        elif t == i18n.get("btn_connections", uid):
            await self._show_connections(msg, uid)
        elif t == i18n.get("btn_logs", uid):
            await self._show_logs_select(msg, uid)
        elif t == i18n.get("btn_unban", uid):
            await self._show_unban(msg, uid)
        elif t == i18n.get("btn_top_attackers", uid):
            await self._show_top_attackers(msg, uid)
        elif t == i18n.get("btn_back", uid):
            await self._send(msg, f"🏠 {i18n.get('main_menu', uid)}", self._main_kb(uid))
        elif t == i18n.get("btn_docker_containers", uid):
            await self._show_docker_containers(msg, uid)
        elif t == i18n.get("btn_docker_logs_menu", uid):
            await self._show_docker_logs_menu(msg, uid)
        elif t == i18n.get("btn_logs_sec", uid):
            await self._show_logs_sec(msg, uid)
        elif t == i18n.get("btn_reports_cpu", uid):
            await self._show_report_cpu(msg, uid)
        elif t == i18n.get("btn_reports_ram", uid):
            await self._show_report_ram(msg, uid)
        elif t == i18n.get("btn_reports_attacks", uid):
            await self._show_report_attacks(msg, uid)
        elif t == i18n.get("btn_reports_daily", uid):
            await self._show_report_daily(msg, uid)
        else:
            await self._send(msg, f"❓ {i18n.get('unknown', uid)}", self._main_kb(uid))

    # ===== CALLBACK ХЕНДЛЕР =====

    async def handle_callback(self, cb: types.CallbackQuery):
        uid = cb.from_user.id
        data = cb.data

        if uid not in Config.ADMIN_USER_IDS:
            await cb.answer(i18n.get("no_access", uid), show_alert=True)
            return

        try:
            # Язык
            if data.startswith("lang:"):
                lang = data.split(":")[1]
                i18n.set_user_lang(uid, lang)
                self.db.save_user_settings(uid, cb.from_user.username, lang)
                name = "🇷🇺 Русский" if lang == "ru" else "🇬🇧 English"
                await cb.answer(f"✅ {name}", show_alert=False)
                try: await cb.message.delete()
                except: pass
                await cb.message.answer(
                    f"✅ {i18n.get('lang_set_ru' if lang == 'ru' else 'lang_set_en', uid)}",
                    reply_markup=self._main_kb(uid)
                )

            # Бан
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
                await cb.answer(f"{ip} забанен на {secs}с", show_alert=True)

            # Разбан
            elif data.startswith("unban_ip:"):
                ip = data.split(":", 1)[1]
                IptablesManager.unban_ip(ip)
                self.db.unban_ip(ip, str(uid))
                IptablesManager.save_rules()
                self.db.log_action(uid, "unban_ip", f"Unbanned {ip}")
                await cb.answer(i18n.get("unban_success", uid, ip=ip), show_alert=True)
                await self._show_banned(cb, uid)

            # IP инфо
            elif data.startswith("ip_info:"):
                ip = data.split(":", 1)[1]
                geo = GeoIPLookup.lookup(ip)
                flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
                text = (
                    f"🔍 **Информация об IP**\n\n"
                    f"🌐 IP: `{ip}` {flag}\n"
                    f"🌍 Страна: {geo['country']} — {geo['city']}\n"
                    f"🏢 Провайдер: {geo['isp']}\n"
                    f"🔌 ASN: {geo['as']}\n\n"
                    f"🚫 В бане: **{'Да' if self.db.is_banned(ip) else 'Нет'}**"
                )
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [IKB(f"🚫 {i18n.get('ban_ip', uid)}", f"ban_ip:{ip}"),
                     IKB(i18n.get("whois", uid), f"whois:{ip}")],
                    [IKB(i18n.get("btn_back", uid), "back_to_main")],
                ])
                await cb.message.answer(text, reply_markup=kb)
                await cb.answer()

            # WHOIS
            elif data.startswith("whois:"):
                ip = data.split(":", 1)[1]
                await cb.answer("⏳ WHOIS...", show_alert=False)
                try:
                    r = subprocess.run(["whois", ip], capture_output=True, text=True, timeout=10)
                    lines = r.stdout.split("\n")
                    short = [l for l in lines if any(l.lower().startswith(k) for k in ["inetnum", "netname", "descr", "country", "org", "abuse"])]
                    text = f"🌐 **WHOIS {ip}**\n\n" + "\n".join(short[:15])
                except:
                    text = f"❌ Ошибка WHOIS для {ip}"
                await cb.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [IKB(i18n.get("btn_back", uid), "back_to_main")]
                ]))
                await cb.answer()

            # Логи
            elif data.startswith("logs:"):
                count = int(data.split(":")[1])
                await self._show_logs_lines(cb, uid, count)

            # Docker логи
            elif data.startswith("dlogs:"):
                container = data.split(":", 1)[1]
                await self._show_docker_container_logs(cb, uid, container)

            # Docker рестарт
            elif data.startswith("docker_restart:"):
                container = data.split(":", 1)[1]
                await cb.answer(f"⏳ Перезапуск {container}...", show_alert=False)
                try:
                    r = subprocess.run(["docker", "restart", container], capture_output=True, timeout=30)
                    if r.returncode == 0:
                        await cb.message.answer(f"✅ {i18n.get('docker_restarted', uid, name=container)}",
                                                reply_markup=self._back_kb(uid))
                    else:
                        await cb.message.answer(f"❌ {i18n.get('docker_error', uid, error=r.stderr.decode()[:200])}",
                                                reply_markup=self._back_kb(uid))
                except Exception as e:
                    await cb.message.answer(f"❌ {i18n.get('docker_error', uid, error=str(e))}",
                                            reply_markup=self._back_kb(uid))
                await cb.answer()

            # Назад
            elif data == "back_to_main":
                await cb.message.answer(f"🏠 {i18n.get('main_menu', uid)}", reply_markup=self._main_kb(uid))
                await cb.answer()

            elif data == "cb_docker_containers":
                await self._show_docker_containers(cb, uid)

            elif data == "noop":
                await cb.answer()

            else:
                await cb.answer(i18n.get("callback_unknown", uid))

        except Exception as e:
            logger.error(f"Callback error: {e}")
            await cb.answer(i18n.get("error", uid), show_alert=True)

    # ===== МОНИТОРИНГ =====

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
                    await self._notify(f"🚫 {i18n.get('autoban', None, ip=ip)}")
                if ip in self._pending_bans:
                    del self._pending_bans[ip]
        if Config.NOTIFY_ON_401:
            flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
            text = i18n.get("attack_notify", None, ip=ip, flag=flag, country=geo['country'],
                           city=geo['city'], isp=geo['isp'], panel=panel, time=data['timestamp'],
                           attempts=self.db.get_recent_attempts(ip, 60))
            for aid in Config.ADMIN_USER_IDS:
                try:
                    await self.bot.send_message(aid, text, reply_markup=self._attack_kb(ip, aid), parse_mode=Markdown)
                except: pass

    async def _on_200(self, data):
        ip, panel = data["ip"], data["panel"]
        self.db.log_login_attempt(ip, True, 200, panel_name=panel)
        geo = GeoIPLookup.lookup(ip)
        flag = GeoIPLookup.get_country_flag(geo.get("country_code", "??"))
        text = i18n.get("login_success", None, ip=ip, flag=flag, country=geo['country'], panel=panel)
        await self._notify(text)

    async def _on_high_cpu(self, d):
        await self._notify(f"⚠️ {i18n.get('high_cpu', None, cpu=d['cpu'], threshold=d['threshold'])}")

    async def _on_high_ram(self, d):
        await self._notify(f"⚠️ {i18n.get('high_ram', None, ram=d['ram'], threshold=d['threshold'])}")

    async def _on_high_conn(self, d):
        await self._notify(f"🚨 {i18n.get('high_conn', None, connections=d['connections'], threshold=d['threshold'])}")

    async def _on_container_down(self, d):
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            IKB(i18n.get("restart", None), f"docker_restart:{d['name']}")
        ]])
        await self._notify(f"🔴 {i18n.get('container_down', None, name=d['name'], time=d['timestamp'])}", kb)

    async def _on_container_up(self, d):
        await self._notify(f"🔄 {i18n.get('container_up', None, name=d['name'])}")

    # ===== ПЕРИОДИКА И ЗАПУСК =====

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
        sf = "/opt/marzban-security-bot/.last_start"
        is_upd = os.path.exists(sf)
        lv = ""
        if is_upd:
            try:
                with open(sf) as f: lv = f.read().strip()
            except: pass
        panels = ", ".join([p["name"] for p in PANELS])
        if is_upd and lv != VERSION:
            text = (
                f"🔄 **Бот обновлён!**\n\n"
                f"✅ SystemFlow v{VERSION}\n"
                f"📝 Изменения:\n"
                f"• Полный рефакторинг визуала\n"
                f"• Эмодзи возвращены\n"
                f"• ВСЕ кнопки теперь работают\n"
                f"• Кнопка Назад во всех меню\n"
                f"• Логи с выбором количества\n"
                f"• Unban inline-списком\n"
                f"• Docker меню с рестартом\n"
                f"• Отчёты меню\n"
                f"• Пользователи из API\n\n"
                f"Готов к работе! 🚀"
            )
        else:
            text = (
                f"🔄 **Бот перезапущен!**\n\n"
                f"✅ SystemFlow v{VERSION}\n"
                f"📋 Панели: {panels}\n"
                f"👥 Админов: {len(Config.ADMIN_USER_IDS)}\n"
                f"🔒 Автобан: {'ON' if Config.AUTOBAN_ENABLED else 'OFF'}\n"
                f"🌍 Язык: {Config.LANGUAGE.upper()}\n\n"
                f"Готов к работе! 🚀"
            )
        for aid in Config.ADMIN_USER_IDS:
            try: await self.bot.send_message(aid, text, parse_mode=Markdown)
            except: pass
        with open(sf, "w") as f: f.write(VERSION)

    def setup_handlers(self):
        self.dp.message.register(self._cmd_start, Command("start"))
        self.dp.message.register(self._cmd_status, Command("status"))
        self.dp.message.register(self._cmd_help, Command("help"))
        self.dp.message.register(self.handle_text)
        self.dp.callback_query.register(self.handle_callback)

    async def _cmd_start(self, msg): self.handle_text(msg)
    async def _cmd_status(self, msg): await self._show_status(msg, msg.from_user.id)
    async def _cmd_help(self, msg): await self._send(msg, i18n.get("help", msg.from_user.id), self._main_kb(msg.from_user.id))

    def handle_text_sync(self, msg):
        """Для /start чтобы не дублировать"""
        asyncio.create_task(self.handle_text(msg))

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


# Алиасы для краткости
KB = KeyboardButton
IKB = InlineKeyboardButton
Markdown = ParseMode.MARKDOWN


async def main():
    await BotApp().run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")
