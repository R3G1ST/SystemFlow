#!/usr/bin/env python3
"""
Система локализации — полный перевод RU/EN без дублирования эмодзи
Эмодзи добавляются в коде, не в переводах заголовков
"""

TRANSLATIONS = {
    "ru": {
        # === Приветствие ===
        "welcome": "Добро пожаловать, {name}!",
        "welcome_sub": "Полный контроль безопасности и мониторинга сервера",
        "welcome_feat": "Возможности:\n• Мониторинг попыток входа в реальном времени\n• Бан IP одним нажатием\n• Статистика и графики атак\n• Управление пользователями Marzban\n• Мониторинг Docker контейнеров\n• Бэкапы с отправкой в чат",
        "select_lang": "Выберите язык:",
        "lang_set_ru": "✅ Язык установлен: Русский",
        "lang_set_en": "✅ Language set to: English",
        "main_menu": "Главное меню",

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
        "btn_logs_sec": "📝 Логи Marzban",
        "btn_unban": "🔓 Разбанить IP",
        "btn_top_attackers": "🏆 ТОП Атакующих",
        "btn_docker_containers": "🐳 Контейнеры",
        "btn_docker_logs_menu": "📝 Логи Docker",
        "btn_reports_cpu": "📊 График CPU",
        "btn_reports_ram": "📊 График RAM",
        "btn_reports_attacks": "📊 График Атак",

        # === Навигация ===
        "btn_back": "↩️ Назад",
        "btn_main_menu": "🏠 Главное меню",

        # === Статус ===
        "server_status": "Статус сервера",
        "cpu_label": "CPU",
        "ram_label": "RAM",
        "disk_label": "Диск",
        "conn_label": "Соединения",
        "uptime_label": "Аптайм",
        "docker_containers": "Docker контейнеры",
        "security_info": "Безопасность",
        "banned_ips": "Забаненные IP",
        "failed_today": "Неудачных попыток сегодня",
        "top_processes": "ТОП Процессы",

        # === Безопасность ===
        "security_menu": "Меню безопасности",
        "banned_list": "Забаненные IP",
        "banned_empty": "Список банов пуст",
        "top_attackers": "ТОП Атакующие",
        "no_attack_data": "Нет данных об атаках",
        "today_stats": "Статистика за сегодня",
        "total_attempts": "Всего попыток",
        "failed_attempts": "Неудачных",
        "success_attempts": "Успешных",
        "unique_ips": "Уникальных IP",
        "audit_log": "Аудит-лог",
        "audit_empty": "Аудит-лог пуст",
        "ban_success": "{ip} забанен!",
        "unban_success": "{ip} разбанен!",
        "already_banned": "{ip} уже забанен!",
        "unban_hint": "Введите IP для разбана:",

        # === Уведомления ===
        "attack_notify": (
            "Попытка неудачного входа\n\n"
            "IP: `{ip}` {flag}\n"
            "Страна: {country} — {city}\n"
            "Провайдер: {isp}\n"
            "Панель: {panel}\n"
            "Время: {time}\n\n"
            "Попыток за последний час: {attempts}"
        ),
        "login_success": (
            "Успешный вход\n\n"
            "IP: `{ip}` {flag}\n"
            "Страна: {country}\n"
            "Панель: {panel}"
        ),
        "autoban": "АВТОБАН: `{ip}` заблокирован автоматически",
        "high_cpu": (
            "Высокая нагрузка CPU\n\n"
            "CPU: {cpu}%\n"
            "Порог: {threshold}%"
        ),
        "high_ram": (
            "Высокая нагрузка RAM\n\n"
            "RAM: {ram}%\n"
            "Порог: {threshold}%"
        ),
        "high_conn": (
            "Много соединений\n\n"
            "Соединения: {connections}\n"
            "Порог: {threshold}\n"
            "Возможна DDoS-атака!"
        ),
        "container_down": (
            "Контейнер упал!\n\n"
            "Контейнер: `{name}`\n"
            "Статус: ОСТАНОВЛЕН\n"
            "Время: {time}"
        ),
        "container_up": (
            "Контейнер перезапущен\n\n"
            "Контейнер: `{name}`\n"
            "Статус: РАБОТАЕТ"
        ),

        # === Inline кнопки ===
        "ban_ip": "БАН",
        "ip_info": "Инфо",
        "ban_1h": "Бан 1ч",
        "ban_24h": "Бан 24ч",
        "whois": "WHOIS",
        "unban_btn": "Разбанить",
        "refresh": "Обновить",
        "restart": "Перезапуск",
        "next_page": "➡️",
        "prev_page": "⬅️",

        # === Соединения ===
        "connections": "Активные соединения",
        "no_connections": "Нет активных соединений",

        # === Логи ===
        "logs_title": "Последние {lines} строк лога",
        "logs_empty": "Логи пусты",
        "logs_hint": "Введите количество строк:",
        "logs_lines": ["10", "25", "50", "100", "200"],

        # === Бэкап ===
        "backup_creating": "Создание бэкапа...",
        "backup_success": "Бэкап создан:\n`{path}`\nРазмер: {size}",
        "backup_failed": "Не удалось создать бэкап",
        "backup_large": "Файл слишком большой для отправки, сохранён на сервере",

        # === Пользователи ===
        "users_title": "Пользователи Marzban",
        "users_need_token": "Для управления пользователями нужен API токен в .env",
        "users_empty": "Список пользователей пуст",

        # === Docker ===
        "docker_title": "Docker контейнеры",
        "docker_running": "Работает",
        "docker_stopped": "Остановлен",
        "docker_restart_confirm": "Перезапустить {name}?",
        "docker_restarted": "Контейнер {name} перезапущен!",
        "docker_error": "Ошибка перезапуска: {error}",
        "docker_logs_title": "Логи контейнера {name}",

        # === Отчёты ===
        "reports_menu": "Меню отчётов",
        "reports_cpu": "График CPU",
        "reports_ram": "График RAM",
        "reports_attacks": "График атак",
        "reports_daily": "📋 Сводка за день",
        "report_generating": "Генерация графика...",
        "report_ready": "График готов:",
        "no_data": "Нет данных для графика",

        # === Настройки ===
        "settings": "Настройки",
        "settings_lang": "Язык",
        "settings_autoban": "Автобан",
        "settings_notify": "Уведомления",

        # === Помощь ===
        "help": (
            "Справка по боту\n\n"
            "Кнопки внизу экрана для навигации.\n\n"
            "Доступные разделы:\n"
            "• Статус — ресурсы сервера\n"
            "• Безопасность — баны, логи, атаки\n"
            "• Пользователи — управление Marzban\n"
            "• Docker — контейнеры\n"
            "• Бэкап — создание резервной копии\n"
            "• Отчёты — графики и статистика\n"
            "• Настройки — язык, уведомления\n"
            "• Забаненные — список блокировок\n"
            "• Соединения — активные подключения\n"
            "• Логи — просмотр логов Marzban"
        ),

        # === Бот ===
        "bot_restarted": (
            "Бот перезапущен!\n\n"
            "SystemFlow v{version} запущен\n"
            "Панели: {panels}\n"
            "Админов: {admins}\n"
            "Автобан: {autoban}\n"
            "Язык: {language}\n\n"
            "Готов к работе!"
        ),
        "bot_updated": (
            "Бот обновлён!\n\n"
            "SystemFlow v{version}\n"
            "Изменения:\n"
            "{changelog}\n\n"
            "Готов к работе!"
        ),

        # === Прочее ===
        "no_access": "У вас нет доступа к этому боту.",
        "error": "Ошибка",
        "loading": "Загрузка...",
        "unknown": "Неизвестная команда. Используйте кнопки:",
        "callback_unknown": "Действие выполняется...",
        "confirm_action": "Подтвердите действие",
    },

    "en": {
        # === Welcome ===
        "welcome": "Welcome, {name}!",
        "welcome_sub": "Complete security control & server monitoring",
        "welcome_feat": "Features:\n• Real-time login monitoring\n• One-click IP ban\n• Attack statistics & charts\n• Marzban user management\n• Docker container monitoring\n• Backups sent to chat",
        "select_lang": "Select language:",
        "lang_set_ru": "✅ Язык установлен: Русский",
        "lang_set_en": "✅ Language set to: English",
        "main_menu": "Main Menu",

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
        "btn_logs_sec": "📝 Marzban Logs",
        "btn_unban": "🔓 Unban IP",
        "btn_top_attackers": "🏆 Top Attackers",
        "btn_docker_containers": "🐳 Containers",
        "btn_docker_logs_menu": "📝 Docker Logs",
        "btn_reports_cpu": "📊 CPU Chart",
        "btn_reports_ram": "📊 RAM Chart",
        "btn_reports_attacks": "📊 Attacks Chart",

        # === Navigation ===
        "btn_back": "↩️ Back",
        "btn_main_menu": "🏠 Main Menu",

        # === Status ===
        "server_status": "Server Status",
        "cpu_label": "CPU",
        "ram_label": "RAM",
        "disk_label": "Disk",
        "conn_label": "Connections",
        "uptime_label": "Uptime",
        "docker_containers": "Docker Containers",
        "security_info": "Security",
        "banned_ips": "Banned IPs",
        "failed_today": "Failed attempts today",
        "top_processes": "Top Processes",

        # === Security ===
        "security_menu": "Security Menu",
        "banned_list": "Banned IPs",
        "banned_empty": "Ban list is empty",
        "top_attackers": "Top Attackers",
        "no_attack_data": "No attack data",
        "today_stats": "Today's Statistics",
        "total_attempts": "Total attempts",
        "failed_attempts": "Failed",
        "success_attempts": "Successful",
        "unique_ips": "Unique IPs",
        "audit_log": "Audit Log",
        "audit_empty": "Audit log is empty",
        "ban_success": "{ip} banned!",
        "unban_success": "{ip} unbanned!",
        "already_banned": "{ip} already banned!",
        "unban_hint": "Enter IP to unban:",

        # === Notifications ===
        "attack_notify": (
            "Failed Login Attempt\n\n"
            "IP: `{ip}` {flag}\n"
            "Country: {country} — {city}\n"
            "ISP: {isp}\n"
            "Panel: {panel}\n"
            "Time: {time}\n\n"
            "Attempts in the last hour: {attempts}"
        ),
        "login_success": (
            "Successful Login\n\n"
            "IP: `{ip}` {flag}\n"
            "Country: {country}\n"
            "Panel: {panel}"
        ),
        "autoban": "AUTOBAN: `{ip}` automatically banned",
        "high_cpu": (
            "High CPU Usage\n\n"
            "CPU: {cpu}%\n"
            "Threshold: {threshold}%"
        ),
        "high_ram": (
            "High RAM Usage\n\n"
            "RAM: {ram}%\n"
            "Threshold: {threshold}%"
        ),
        "high_conn": (
            "High Connections Count\n\n"
            "Connections: {connections}\n"
            "Threshold: {threshold}\n"
            "Possible DDoS attack!"
        ),
        "container_down": (
            "Container Down!\n\n"
            "Container: `{name}`\n"
            "Status: STOPPED\n"
            "Time: {time}"
        ),
        "container_up": (
            "Container Restarted\n\n"
            "Container: `{name}`\n"
            "Status: RUNNING"
        ),

        # === Inline Buttons ===
        "ban_ip": "BAN",
        "ip_info": "Info",
        "ban_1h": "Ban 1h",
        "ban_24h": "Ban 24h",
        "whois": "WHOIS",
        "unban_btn": "Unban",
        "refresh": "Refresh",
        "restart": "Restart",
        "next_page": "➡️",
        "prev_page": "⬅️",

        # === Connections ===
        "connections": "Active Connections",
        "no_connections": "No active connections",

        # === Logs ===
        "logs_title": "Last {lines} log lines",
        "logs_empty": "Logs are empty",
        "logs_hint": "Enter number of lines:",
        "logs_lines": ["10", "25", "50", "100", "200"],

        # === Backup ===
        "backup_creating": "Creating backup...",
        "backup_success": "Backup created:\n`{path}`\nSize: {size}",
        "backup_failed": "Failed to create backup",
        "backup_large": "File too large to send, saved on server",

        # === Users ===
        "users_title": "Marzban Users",
        "users_need_token": "API token required in .env for user management",
        "users_empty": "User list is empty",

        # === Docker ===
        "docker_title": "Docker Containers",
        "docker_running": "Running",
        "docker_stopped": "Stopped",
        "docker_restart_confirm": "Restart {name}?",
        "docker_restarted": "Container {name} restarted!",
        "docker_error": "Restart error: {error}",
        "docker_logs_title": "Container {name} logs",

        # === Reports ===
        "reports_menu": "Reports Menu",
        "reports_cpu": "CPU Chart",
        "reports_ram": "RAM Chart",
        "reports_attacks": "Attacks Chart",
        "reports_daily": "📋 Daily Summary",
        "report_generating": "Generating chart...",
        "report_ready": "Chart ready:",
        "no_data": "No data for chart",

        # === Settings ===
        "settings": "Settings",
        "settings_lang": "Language",
        "settings_autoban": "Autoban",
        "settings_notify": "Notifications",

        # === Help ===
        "help": (
            "Bot Help\n\n"
            "Use buttons at the bottom for navigation.\n\n"
            "Available sections:\n"
            "• Status — server resources\n"
            "• Security — bans, logs, attacks\n"
            "• Users — Marzban management\n"
            "• Docker — containers\n"
            "• Backup — create a backup\n"
            "• Reports — charts & statistics\n"
            "• Settings — language, notifications\n"
            "• Banned — blocklist\n"
            "• Connections — active connections\n"
            "• Logs — Marzban log viewer"
        ),

        # === Bot ===
        "bot_restarted": (
            "Bot Restarted!\n\n"
            "SystemFlow v{version} started\n"
            "Panels: {panels}\n"
            "Admins: {admins}\n"
            "Autoban: {autoban}\n"
            "Language: {language}\n\n"
            "Ready to work!"
        ),
        "bot_updated": (
            "Bot Updated!\n\n"
            "SystemFlow v{version}\n"
            "Changes:\n"
            "{changelog}\n\n"
            "Ready to work!"
        ),

        # === Misc ===
        "no_access": "You don't have access to this bot.",
        "error": "Error",
        "loading": "Loading...",
        "unknown": "Unknown command. Use buttons:",
        "callback_unknown": "Action processing...",
        "confirm_action": "Confirm action",
    }
}


class Localization:
    def __init__(self, default_lang: str = "ru"):
        self.default_lang = default_lang
        self.user_langs: dict = {}

    def set_user_lang(self, telegram_id: int, lang: str):
        if lang in TRANSLATIONS:
            self.user_langs[telegram_id] = lang

    def get_user_lang(self, telegram_id: int) -> str:
        return self.user_langs.get(telegram_id, self.default_lang)

    def get(self, key: str, telegram_id: int = None, **kwargs) -> str:
        lang = self.get_user_lang(telegram_id) if telegram_id else self.default_lang
        text = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

    def get_available_langs(self) -> list:
        return list(TRANSLATIONS.keys())


i18n = Localization()
