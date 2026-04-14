#!/usr/bin/env python3
"""
Утилиты: управление iptables, GeoIP, бэкапы, Marzban API
"""
import subprocess
import os
import json
import requests
from typing import Optional, Dict, List
from datetime import datetime


class IptablesManager:
    """Управление фаерволом iptables"""

    @staticmethod
    def ban_ip(ip: str, comment: str = "marzban-bot") -> bool:
        """Заблокировать IP"""
        try:
            # Проверяем, не заблокирован ли уже
            check = subprocess.run(
                ["iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"],
                capture_output=True, timeout=10
            )
            if check.returncode != 0:
                subprocess.run(
                    ["iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"],
                    capture_output=True, timeout=10
                )
            return True
        except Exception as e:
            print(f"[IPTABLES] Ban error: {e}")
            return False

    @staticmethod
    def unban_ip(ip: str) -> bool:
        """Разблокировать IP"""
        try:
            subprocess.run(
                ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
                capture_output=True, timeout=10
            )
            return True
        except Exception as e:
            print(f"[IPTABLES] Unban error: {e}")
            return False

    @staticmethod
    def get_banned_ips() -> List[str]:
        """Получить список забаненных IP из iptables"""
        try:
            result = subprocess.run(
                ["iptables", "-L", "INPUT", "-n"],
                capture_output=True, text=True, timeout=10
            )
            ips = []
            for line in result.stdout.split("\n"):
                if "DROP" in line:
                    parts = line.split()
                    for part in parts:
                        if "." in part and "/" in part:
                            ips.append(part.split("/")[0])
                        elif "." in part and all(c.isdigit() or c == "." for c in part):
                            ips.append(part)
            return ips
        except Exception as e:
            print(f"[IPTABLES] Get banned error: {e}")
            return []

    @staticmethod
    def save_rules() -> bool:
        """Сохранить правила"""
        try:
            os.makedirs("/etc/iptables", exist_ok=True)
            subprocess.run(
                "iptables-save > /etc/iptables/rules.v4",
                shell=True, timeout=10
            )
            return True
        except Exception as e:
            print(f"[IPTABLES] Save error: {e}")
            return False


class GeoIPLookup:
    """GeoIP определение - без внешних API, через встроенную базу"""

    GEOIP_DB_URL = "https://ip-api.com/json/"

    @classmethod
    def lookup(cls, ip: str) -> Dict:
        """Получить информацию об IP"""
        try:
            # Используем ip-api.com (бесплатный, без ключа)
            response = requests.get(
                f"{cls.GEOIP_DB_URL}{ip}?fields=status,country,countryCode,regionName,city,isp,org,as,query",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "country": data.get("country", "Unknown"),
                        "country_code": data.get("countryCode", "??"),
                        "city": data.get("city", "Unknown"),
                        "isp": data.get("isp", "Unknown"),
                        "org": data.get("org", "Unknown"),
                        "as": data.get("as", "Unknown"),
                        "query": data.get("query", ip),
                    }
        except Exception as e:
            print(f"[GEOIP] Lookup error: {e}")

        return {
            "country": "Unknown",
            "country_code": "??",
            "city": "Unknown",
            "isp": "Unknown",
            "org": "Unknown",
            "as": "Unknown",
            "query": ip,
        }

    @classmethod
    def get_country_flag(cls, country_code: str) -> str:
        """Получить флаг страны"""
        if not country_code or country_code == "??":
            return "🌍"
        try:
            offset = 127397
            return chr(ord(country_code[0].upper()) + offset) + chr(ord(country_code[1].upper()) + offset)
        except:
            return "🌍"


class BackupManager:
    """Управление бэкапами Marzban"""

    @staticmethod
    def create_backup(backup_dir: str = "/opt/marzban-security-bot/backups") -> Optional[str]:
        """Создать бэкап базы данных Marzban"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"marzban_backup_{timestamp}.tar.gz")

            # Бэкап через Docker
            result = subprocess.run(
                ["docker", "exec", "marzban-marzban-1", "marzban", "backup"],
                capture_output=True, timeout=60
            )

            if result.returncode == 0:
                # Копируем бэкап из контейнера
                subprocess.run(
                    ["docker", "cp", f"marzban-marzban-1:/var/lib/marzban/backups/{timestamp}.tar.gz", backup_file],
                    capture_output=True, timeout=30
                )
                return backup_file

            # Fallback: бэкап папки Marzban
            subprocess.run(
                f"tar -czf {backup_file} /var/lib/marzban 2>/dev/null",
                shell=True, timeout=120
            )

            if os.path.exists(backup_file):
                return backup_file

        except Exception as e:
            print(f"[BACKUP] Error: {e}")

        return None

    @staticmethod
    def get_backups(backup_dir: str = "/opt/marzban-security-bot/backups") -> List[Dict]:
        """Получить список бэкапов"""
        backups = []
        try:
            if os.path.exists(backup_dir):
                for f in sorted(os.listdir(backup_dir), reverse=True):
                    if f.endswith(".tar.gz"):
                        path = os.path.join(backup_dir, f)
                        size = os.path.getsize(path)
                        mtime = datetime.fromtimestamp(os.path.getmtime(path))
                        backups.append({
                            "filename": f,
                            "path": path,
                            "size": size,
                            "size_human": BackupManager._format_size(size),
                            "created": mtime.strftime("%Y-%m-%d %H:%M"),
                        })
        except Exception as e:
            print(f"[BACKUP] List error: {e}")
        return backups

    @staticmethod
    def _format_size(size: int) -> str:
        """Форматировать размер файла"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @staticmethod
    def cleanup_old(backup_dir: str = "/opt/marzban-security-bot/backups", keep: int = 10):
        """Удалить старые бэкапы"""
        try:
            backups = sorted(
                [f for f in os.listdir(backup_dir) if f.endswith(".tar.gz")],
                key=lambda x: os.path.getmtime(os.path.join(backup_dir, x))
            )
            for f in backups[:-keep]:
                os.remove(os.path.join(backup_dir, f))
        except Exception as e:
            print(f"[BACKUP] Cleanup error: {e}")


class MarzbanAPI:
    """API для взаимодействия с панелью Marzban"""

    def __init__(self, base_url: str = "http://localhost:8000", api_token: str = None):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self._token = None
        self._token_expires = 0

    def _get_headers(self) -> Dict:
        """Получить заголовки для запросов"""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def authenticate(self, username: str, password: str) -> bool:
        """Аутентификация в API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/admin/token",
                data={"username": username, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self._token = data.get("access_token")
                return True
        except Exception as e:
            print(f"[MARZBAN-API] Auth error: {e}")
        return False

    def get_users(self) -> List[Dict]:
        """Получить список пользователей"""
        try:
            response = requests.get(
                f"{self.base_url}/api/users",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[MARZBAN-API] Get users error: {e}")
        return []

    def get_user(self, username: str) -> Optional[Dict]:
        """Получить пользователя"""
        try:
            response = requests.get(
                f"{self.base_url}/api/users/{username}",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[MARZBAN-API] Get user error: {e}")
        return None

    def reset_user_data(self, username: str) -> bool:
        """Сбросить трафик пользователя"""
        try:
            response = requests.post(
                f"{self.base_url}/api/users/{username}/reset",
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[MARZBAN-API] Reset error: {e}")
            return False

    def disable_user(self, username: str) -> bool:
        """Отключить пользователя"""
        try:
            response = requests.put(
                f"{self.base_url}/api/users/{username}",
                headers=self._get_headers(),
                json={"status": "disabled"},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[MARZBAN-API] Disable error: {e}")
            return False

    def get_system_stats(self) -> Optional[Dict]:
        """Получить статистику системы"""
        try:
            response = requests.get(
                f"{self.base_url}/api/system",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[MARZBAN-API] System stats error: {e}")
        return None

    def get_inbounds(self) -> List[Dict]:
        """Получить inbound-ы"""
        try:
            response = requests.get(
                f"{self.base_url}/api/inbounds",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[MARZBAN-API] Inbounds error: {e}")
        return []
