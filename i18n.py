#!/usr/bin/env python3
"""
Полная система локализации — Русский + English
"""

TRANSLATIONS = {
    "ru": {
        # === Приветствие и меню ===
        "welcome_title": "👋 **Добро пожаловать, {name}!**",
        "welcome_subtitle": "🛡️ **SystemFlow v3.0**\nПолный контроль безопасности и мониторинга сервера",
        "welcome_features": (
            "📋 **Возможности:**\n"
            "🔐 Мониторинг попыток входа в реальном времени\n"
            "🚫 Бан IP одной кнопкой\n"
            "📊 Статистика и графики атак\n"
            "👥 Управление пользователями Marzban\n"
            "🐳 Мониторинг Docker контейнеров\n"
            "💾 Бэкапы с отправкой в чат\n\n"
            "Выберите язык / Select language:"
        ),
        "main_menu": "📱 **Главное меню**",
        "select_language": "🌍 Выберите язык:",
        "language_set": "✅ Язык установлен: Русский",

        # === Reply кнопки ===
        "btn_status": "📊 Статус",
        "btn_security": "🔒 Безопасность",
        "btn_users": "👥 Пользователи",
        "btn_docker": "🐳 Docker",
        "btn_backup": "💾 Бэкап",
        "btn_reports": "📈 Отчёты",
        "btn_settings": "⚙️ Настройки",
        "btn_help": "❓ Помощь",
        "btn_banned": "🚫 Забаненные",
        "btn_connections": "🔌 Соединения",
        "btn_logs": "📝 Логи",

        # === Команды ===
        "cmd_status_title": "📊 Статус сервера",
        "cmd_security_title": "🔒 Безопасность",
        "cmd_users_title": "👥 Пользователи",
        "cmd_docker_title": "🐳 Docker контейнеры",
        "cmd_backup_title": "💾 Бэкап",
        "cmd_reports_title": "📈 Отчёты",

        # === Статус ===
        "server_status": "📊 **Статус сервера**",
        "cpu": "🔴 CPU",
        "ram": "🟢 RAM",
        "disk": "💾 Диск",
        "connections": "🔌 Соединения",
        "uptime": "⏱️ Аптайм",
        "docker_containers": "🐳 **Docker контейнеры**",
        "security_info": "🛡️ **Безопасность**",
        "banned_ips": "🚫 Забаненные IP",
        "failed_today": "🔐 Неудачных попыток сегодня",
        "top_processes": "🔝 **ТОП Процессы**",

        # === Безопасность ===
        "security_menu_title": "🔒 **Меню безопасности**",
        "banned_list_title": "🚫 **Забаненные IP**",
        "banned_list_empty": "✅ Список банов пуст",
        "top_attackers_title": "🏆 **ТОП Атакующие**",
        "no_attack_data": "📊 Нет данных об атаках",
        "today_stats_title": "📊 **Статистика за сегодня**",
        "total_attempts": "🔐 Всего попыток",
        "failed_attempts": "❌ Неудачных",
        "success_attempts": "✅ Успешных",
        "unique_ips": "🌐 Уникальных IP",
        "audit_log_title": "📝 **Аудит-лог**",
        "audit_log_empty": "📝 Аудит-лог пуст",
        "ban_ip_success": "🚫 **{ip}** забанен!",
        "unban_ip_success": "✅ **{ip}** разбанен!",
        "ip_already_banned": "✅ **{ip}** уже забанен!",
        "unban_command": "Использование: `/unban <ip>`",

        # === Уведомления об атаках ===
        "attack_notification": (
            "🚨 **Попытка неудачного входа**\n\n"
            "🌐 IP: `{ip}` {flag}\n"
            "🌍 Страна: {country} — {city}\n"
            "🏢 Провайдер: {isp}\n"
            "🖥️ Панель: {panel}\n"
            "🕐 Время: {time}\n\n"
            "⚠️ Попыток за последний час: **{attempts}**"
        ),
        "successful_login": (
            "✅ **Успешный вход**\n\n"
            "🌐 IP: `{ip}` {flag}\n"
            "🌍 Страна: {country}\n"
            "🖥️ Панель: {panel}"
        ),
        "autoban_notification": "🚫 **АВТОБАН**: `{ip}` заблокирован автоматически",
        "high_cpu_alert": (
            "⚠️ **Высокая нагрузка CPU**\n\n"
            "🔴 CPU: **{cpu}%**\n"
            "📊 Порог: {threshold}%"
        ),
        "high_ram_alert": (
            "⚠️ **Высокая нагрузка RAM**\n\n"
            "🔴 RAM: **{ram}%**\n"
            "📊 Порог: {threshold}%"
        ),
        "high_connections_alert": (
            "⚠️ **Много соединений**\n\n"
            "🔌 Соединения: **{connections}**\n"
            "📊 Порог: {threshold}\n"
            "🚨 Возможна DDoS-атака!"
        ),
        "container_down": (
            "🔴 **Контейнер упал!**\n\n"
            "🐳 Контейнер: `{name}`\n"
            "⚠️ Статус: ОСТАНОВЛЕН\n"
            "🕐 Время: {time}"
        ),
        "container_restart": (
            "🔄 **Контейнер перезапущен**\n\n"
            "🐳 Контейнер: `{name}`\n"
            "✅ Статус: РАБОТАЕТ"
        ),

        # === Соединения ===
        "connections_title": "🔌 **Активные соединения**",

        # === Логи ===
        "logs_title": "📝 **Последние {lines} строк лога:**",
        "logs_empty": "📝 Логи пусты",

        # === Бэкап ===
        "backup_creating": "⏳ Создание бэкапа...",
        "backup_success": "✅ Бэкап создан:\n📁 `{path}`\n📦 Размер: {size}",
        "backup_failed": "❌ Не удалось создать бэкап",
        "backup_too_large": "⚠️ Файл слишком большой для отправки, сохранён на сервере",

        # === Inline кнопки ===
        "btn_ban_ip": "🚫 БАН",
        "btn_ip_info": "🔍 Инфо",
        "btn_ban_1h": "⏳ Бан 1ч",
        "btn_ban_24h": "⏳ Бан 24ч",
        "btn_whitelist": "✅ В белый список",
        "btn_whois": "🌐 WHOIS",
        "btn_refresh": "🔄 Обновить",
        "btn_ban_permanent": "🚫 Бан навсегда",
        "btn_restart_container": "🔄 Перезапуск",

        # === Настройки ===
        "settings_title": "⚙️ Настройки",
        "settings_language": "🌍 Язык",
        "settings_notifications": "🔔 Уведомления",
        "settings_autoban": "🚫 Автобан",
        "settings_language_select": "🌍 Выберите язык / Select language:",

        # === Помощь ===
        "help_title": "📖 **Справка по командам**",
        "help_text": (
            "/start — Главное меню\n"
            "/status — Статус сервера\n"
            "/security — Меню безопасности\n"
            "/users — Пользователи Marzban\n"
            "/docker — Docker контейнеры\n"
            "/backup — Создать бэкап\n"
            "/banned — Список забаненных\n"
            "/unban <ip> — Разбанить IP\n"
            "/logs [n] — Последние N логов\n"
            "/connections — Активные соединения\n"
            "/reports — Отчёты\n"
            "/help — Эта справка"
        ),

        # === Бот ===
        "bot_restarted": (
            "🔄 **Бот перезапущен!**\n\n"
            "✅ SystemFlow v{version} запущен\n"
            "📋 Панели: {panels}\n"
            "👥 Админов: {admins}\n"
            "🔒 Автобан: {autoban}\n"
            "🌍 Язык: {language}\n\n"
            "Готов к работе! 🚀"
        ),
        "bot_updated": (
            "🔄 **Бот обновлён!**\n\n"
            "✅ SystemFlow v{version}\n"
            "📝 Изменения:\n"
            "{changelog}\n\n"
            "Готов к работе! 🚀"
        ),

        # === Прочее ===
        "no_access": "❌ У вас нет доступа к этому боту.",
        "error": "❌ Ошибка",
        "loading": "⏳ Загрузка...",
        "unknown_command": "❓ Неизвестная команда",
        "callback_processing": "⏳ Обработка...",
    },

    "en": {
        # === Welcome & Menu ===
        "welcome_title": "👋 **Welcome, {name}!**",
        "welcome_subtitle": "🛡️ **SystemFlow v3.0**\nComplete security control & server monitoring",
        "welcome_features": (
            "📋 **Features:**\n"
            "🔐 Real-time login attempt monitoring\n"
            "🚫 One-click IP ban\n"
            "📊 Attack statistics & charts\n"
            "👥 Marzban user management\n"
            "🐳 Docker container monitoring\n"
            "💾 Backups sent to chat\n\n"
            "Select your language:"
        ),
        "main_menu": "📱 **Main Menu**",
        "select_language": "🌍 Select language:",
        "language_set": "✅ Language set to: English",

        # === Reply Buttons ===
        "btn_status": "📊 Status",
        "btn_security": "🔒 Security",
        "btn_users": "👥 Users",
        "btn_docker": "🐳 Docker",
        "btn_backup": "💾 Backup",
        "btn_reports": "📈 Reports",
        "btn_settings": "⚙️ Settings",
        "btn_help": "❓ Help",
        "btn_banned": "🚫 Banned",
        "btn_connections": "🔌 Connections",
        "btn_logs": "📝 Logs",

        # === Commands ===
        "cmd_status_title": "📊 Server Status",
        "cmd_security_title": "🔒 Security",
        "cmd_users_title": "👥 Users",
        "cmd_docker_title": "🐳 Docker Containers",
        "cmd_backup_title": "💾 Backup",
        "cmd_reports_title": "📈 Reports",

        # === Status ===
        "server_status": "📊 **Server Status**",
        "cpu": "🔴 CPU",
        "ram": "🟢 RAM",
        "disk": "💾 Disk",
        "connections": "🔌 Connections",
        "uptime": "⏱️ Uptime",
        "docker_containers": "🐳 **Docker Containers**",
        "security_info": "🛡️ **Security**",
        "banned_ips": "🚫 Banned IPs",
        "failed_today": "🔐 Failed attempts today",
        "top_processes": "🔝 **Top Processes**",

        # === Security ===
        "security_menu_title": "🔒 **Security Menu**",
        "banned_list_title": "🚫 **Banned IPs**",
        "banned_list_empty": "✅ Ban list is empty",
        "top_attackers_title": "🏆 **Top Attackers**",
        "no_attack_data": "📊 No attack data",
        "today_stats_title": "📊 **Today's Statistics**",
        "total_attempts": "🔐 Total attempts",
        "failed_attempts": "❌ Failed",
        "success_attempts": "✅ Successful",
        "unique_ips": "🌐 Unique IPs",
        "audit_log_title": "📝 **Audit Log**",
        "audit_log_empty": "📝 Audit log is empty",
        "ban_ip_success": "🚫 **{ip}** banned!",
        "unban_ip_success": "✅ **{ip}** unbanned!",
        "ip_already_banned": "✅ **{ip}** already banned!",
        "unban_command": "Usage: `/unban <ip>`",

        # === Attack Notifications ===
        "attack_notification": (
            "🚨 **Failed Login Attempt**\n\n"
            "🌐 IP: `{ip}` {flag}\n"
            "🌍 Country: {country} — {city}\n"
            "🏢 ISP: {isp}\n"
            "🖥️ Panel: {panel}\n"
            "🕐 Time: {time}\n\n"
            "⚠️ Attempts in the last hour: **{attempts}**"
        ),
        "successful_login": (
            "✅ **Successful Login**\n\n"
            "🌐 IP: `{ip}` {flag}\n"
            "🌍 Country: {country}\n"
            "🖥️ Panel: {panel}"
        ),
        "autoban_notification": "🚫 **AUTOBAN**: `{ip}` automatically banned",
        "high_cpu_alert": (
            "⚠️ **High CPU Usage**\n\n"
            "🔴 CPU: **{cpu}%**\n"
            "📊 Threshold: {threshold}%"
        ),
        "high_ram_alert": (
            "⚠️ **High RAM Usage**\n\n"
            "🔴 RAM: **{ram}%**\n"
            "📊 Threshold: {threshold}%"
        ),
        "high_connections_alert": (
            "⚠️ **High Connections Count**\n\n"
            "🔌 Connections: **{connections}**\n"
            "📊 Threshold: {threshold}\n"
            "🚨 Possible DDoS attack!"
        ),
        "container_down": (
            "🔴 **Container Down!**\n\n"
            "🐳 Container: `{name}`\n"
            "⚠️ Status: STOPPED\n"
            "🕐 Time: {time}"
        ),
        "container_restart": (
            "🔄 **Container Restarted**\n\n"
            "🐳 Container: `{name}`\n"
            "✅ Status: RUNNING"
        ),

        # === Connections ===
        "connections_title": "🔌 **Active Connections**",

        # === Logs ===
        "logs_title": "📝 **Last {lines} log lines:**",
        "logs_empty": "📝 Logs are empty",

        # === Backup ===
        "backup_creating": "⏳ Creating backup...",
        "backup_success": "✅ Backup created:\n📁 `{path}`\n📦 Size: {size}",
        "backup_failed": "❌ Failed to create backup",
        "backup_too_large": "⚠️ File too large to send, saved on server",

        # === Inline Buttons ===
        "btn_ban_ip": "🚫 BAN",
        "btn_ip_info": "🔍 Info",
        "btn_ban_1h": "⏳ Ban 1h",
        "btn_ban_24h": "⏳ Ban 24h",
        "btn_whitelist": "✅ Whitelist",
        "btn_whois": "🌐 WHOIS",
        "btn_refresh": "🔄 Refresh",
        "btn_ban_permanent": "🚫 Permaban",
        "btn_restart_container": "🔄 Restart",

        # === Settings ===
        "settings_title": "⚙️ Settings",
        "settings_language": "🌍 Language",
        "settings_notifications": "🔔 Notifications",
        "settings_autoban": "🚫 Autoban",
        "settings_language_select": "🌍 Select language / Выберите язык:",

        # === Help ===
        "help_title": "📖 **Command Reference**",
        "help_text": (
            "/start — Main menu\n"
            "/status — Server status\n"
            "/security — Security menu\n"
            "/users — Marzban users\n"
            "/docker — Docker containers\n"
            "/backup — Create backup\n"
            "/banned — Banned IPs list\n"
            "/unban <ip> — Unban IP\n"
            "/logs [n] — Last N log lines\n"
            "/connections — Active connections\n"
            "/reports — Reports\n"
            "/help — This help"
        ),

        # === Bot ===
        "bot_restarted": (
            "🔄 **Bot Restarted!**\n\n"
            "✅ SystemFlow v{version} started\n"
            "📋 Panels: {panels}\n"
            "👥 Admins: {admins}\n"
            "🔒 Autoban: {autoban}\n"
            "🌍 Language: {language}\n\n"
            "Ready to work! 🚀"
        ),
        "bot_updated": (
            "🔄 **Bot Updated!**\n\n"
            "✅ SystemFlow v{version}\n"
            "📝 Changes:\n"
            "{changelog}\n\n"
            "Ready to work! 🚀"
        ),

        # === Misc ===
        "no_access": "❌ You don't have access to this bot.",
        "error": "❌ Error",
        "loading": "⏳ Loading...",
        "unknown_command": "❓ Unknown command",
        "callback_processing": "⏳ Processing...",
    }
}


class Localization:
    """Менеджер локализации"""

    def __init__(self, default_lang: str = "ru"):
        self.default_lang = default_lang
        self.user_langs: dict = {}  # telegram_id -> lang

    def set_user_lang(self, telegram_id: int, lang: str):
        """Установить язык пользователя"""
        if lang in TRANSLATIONS:
            self.user_langs[telegram_id] = lang

    def get_user_lang(self, telegram_id: int) -> str:
        """Получить язык пользователя"""
        return self.user_langs.get(telegram_id, self.default_lang)

    def get(self, key: str, telegram_id: int = None, **kwargs) -> str:
        """Получить перевод"""
        lang = self.get_user_lang(telegram_id) if telegram_id else self.default_lang
        text = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

    def get_available_langs(self) -> list:
        """Получить список доступных языков"""
        return list(TRANSLATIONS.keys())

    def get_language_button(self, telegram_id: int = None) -> str:
        """Получить кнопку выбора языка"""
        return self.get("settings_language_select", telegram_id)


# Глобальный экземпляр
i18n = Localization()
