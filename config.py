#!/usr/bin/env python3
"""
Универсальная конфигурация для Marzban Security Bot
Поддержка любой панели Marzban на Ubuntu сервере
"""
import os
import subprocess
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()


class Config:
    """Основная конфигурация"""

    # Telegram Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    ADMIN_USER_IDS = [
        int(x.strip()) for x in os.getenv("ADMIN_USER_IDS", "0").split(",") if x.strip()
    ]

    # Marzban - автоопределение если не задано
    MARZBAN_DOCKER_HOST = os.getenv("MARZBAN_DOCKER_HOST", "localhost")

    # Поддержка нескольких панелей (имя_контейнера:URL через запятую)
    # Пример: "marzban-marzban-1:https://panel1.com,marzban2-marzban-1:https://panel2.com"
    MULTI_PANELS = os.getenv("MULTI_PANELS", "")

    # Безопасность
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "3"))
    BAN_TIME_WINDOW = int(os.getenv("BAN_TIME_WINDOW", "300"))  # 5 минут
    AUTOBAN_ENABLED = os.getenv("AUTOBAN_ENABLED", "true").lower() == "true"

    # Уведомления
    NOTIFY_ON_401 = os.getenv("NOTIFY_ON_401", "true").lower() == "true"
    NOTIFY_ON_BAN = os.getenv("NOTIFY_ON_BAN", "true").lower() == "true"
    NOTIFY_ON_HIGH_CPU = os.getenv("NOTIFY_ON_HIGH_CPU", "true").lower() == "true"
    NOTIFY_ON_HIGH_RAM = os.getenv("NOTIFY_ON_HIGH_RAM", "true").lower() == "true"
    CPU_THRESHOLD = int(os.getenv("CPU_THRESHOLD", "80"))
    RAM_THRESHOLD = int(os.getenv("RAM_THRESHOLD", "90"))
    CONNECTIONS_THRESHOLD = int(os.getenv("CONNECTIONS_THRESHOLD", "500"))

    # Мониторинг
    MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "3"))  # секунды
    SYSTEM_CHECK_INTERVAL = int(os.getenv("SYSTEM_CHECK_INTERVAL", "30"))  # секунды

    # GeoIP
    GEOIP_ENABLED = os.getenv("GEOIP_ENABLED", "true").lower() == "true"

    # Бэкапы
    BACKUP_DIR = os.getenv("BACKUP_DIR", "/opt/marzban-security-bot/backups")
    AUTO_BACKUP_ENABLED = os.getenv("AUTO_BACKUP_ENABLED", "false").lower() == "true"
    BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))

    # Локализация
    LANGUAGE = os.getenv("LANGUAGE", "ru")  # ru, en, fa

    # Режимы
    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"  # Тестовый режим без бана
    VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"  # Подробные логи


class PanelConfig:
    """Конфигурация панели Marzban - автоопределение"""

    @staticmethod
    def discover_marzban_panels() -> List[Dict]:
        """Автоматически найти все панели Marzban на сервере"""
        panels = []

        try:
            # Ищем все Docker контейнеры с marzban в имени
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=marzban", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                containers = [c.strip() for c in result.stdout.strip().split("\n") if c.strip()]
                for container in containers:
                    panels.append({
                        "name": container,
                        "url": "http://localhost",
                        "container": container
                    })
        except Exception as e:
            print(f"[CONFIG] Auto-discover error: {e}")

        # Если мульти-панели заданы вручную
        if Config.MULTI_PANELS:
            panels = []
            for panel_str in Config.MULTI_PANELS.split(","):
                if ":" in panel_str:
                    name, url = panel_str.split(":", 1)
                    panels.append({
                        "name": name.strip(),
                        "url": url.strip(),
                        "container": name.strip()
                    })

        # Если ничего не найдено - используем дефолт
        if not panels:
            panels.append({
                "name": "marzban-marzban-1",
                "url": "http://localhost",
                "container": "marzban-marzban-1"
            })

        return panels

    @staticmethod
    def get_panel_api_token(panel_name: str) -> Optional[str]:
        """Получить API токен для панели из env"""
        # MARZBAN_API_TOKEN_MARZBAN_MARBAN_1
        key = f"MARZBAN_API_TOKEN_{panel_name.upper().replace('-', '_')}"
        return os.getenv(key)


# Инициализация
PANELS = PanelConfig.discover_marzban_panels()
DEFAULT_PANEL = PANELS[0]["name"] if PANELS else None
