#!/usr/bin/env python3
"""
База данных бота - SQLite
Хранит: баны, статистику атак, настройки пользователей, логи аудита
"""
import sqlite3
import os
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "/opt/marzban-security-bot/bot.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        """Инициализация таблиц"""
        with self._get_conn() as conn:
            # Заблокированные IP
            conn.execute("""
                CREATE TABLE IF NOT EXISTS banned_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT UNIQUE NOT NULL,
                    reason TEXT DEFAULT 'Brute force',
                    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    banned_by TEXT DEFAULT 'autoban',
                    ban_type TEXT DEFAULT 'permanent',
                    unbanned_at TIMESTAMP NULL,
                    panel_name TEXT DEFAULT 'all'
                )
            """)

            # Попытки входа
            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT NOT NULL,
                    username TEXT,
                    success BOOLEAN DEFAULT 0,
                    status_code INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    panel_name TEXT DEFAULT 'all',
                    country TEXT,
                    user_agent TEXT
                )
            """)

            # Индексы для быстрого поиска
            conn.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_banned_ips_ip ON banned_ips(ip)")

            # Статистика атак по дням
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attack_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    country TEXT,
                    attempts INTEGER DEFAULT 1,
                    UNIQUE(date, ip)
                )
            """)

            # Системные метрики (CPU, RAM и т.д.)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    ram_percent REAL,
                    disk_percent REAL,
                    connections INTEGER,
                    network_in_bytes INTEGER,
                    network_out_bytes INTEGER
                )
            """)

            # Настройки пользователей бота
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    role TEXT DEFAULT 'admin',
                    notifications_enabled BOOLEAN DEFAULT 1,
                    language TEXT DEFAULT 'ru',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Аудит-лог действий
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT
                )
            """)

            # Бэкапы
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    size_bytes INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'success'
                )
            """)

            # Сессии пользователей
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    command TEXT,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    # === BAN IP ===

    def ban_ip(self, ip: str, reason: str = "Brute force",
               banned_by: str = "autoban", ban_type: str = "permanent",
               panel_name: str = "all") -> bool:
        """Заблокировать IP"""
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO banned_ips (ip, reason, banned_by, ban_type, panel_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (ip, reason, banned_by, ban_type, panel_name))
            return True
        except Exception as e:
            print(f"[DB] Ban error: {e}")
            return False

    def unban_ip(self, ip: str, unbanned_by: str = "admin") -> bool:
        """Разблокировать IP"""
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    UPDATE banned_ips SET unbanned_at = CURRENT_TIMESTAMP
                    WHERE ip = ? AND unbanned_at IS NULL
                """, (ip,))
            return True
        except Exception as e:
            print(f"[DB] Unban error: {e}")
            return False

    def is_banned(self, ip: str) -> bool:
        """Проверить, забанен ли IP"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM banned_ips WHERE ip = ? AND unbanned_at IS NULL",
                (ip,)
            ).fetchone()
            return row is not None

    def get_banned_ips(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Получить список забаненных IP"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM banned_ips
                WHERE unbanned_at IS NULL
                ORDER BY banned_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()
            return [dict(r) for r in rows]

    def get_banned_count(self) -> int:
        """Количество забаненных IP"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM banned_ips WHERE unbanned_at IS NULL"
            ).fetchone()
            return row["cnt"] if row else 0

    # === LOGIN ATTEMPTS ===

    def log_login_attempt(self, ip: str, success: bool = False,
                          status_code: int = 401, username: str = None,
                          panel_name: str = "all", country: str = None,
                          user_agent: str = None):
        """Записать попытку входа"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO login_attempts (ip, username, success, status_code, panel_name, country, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ip, username, success, status_code, panel_name, country, user_agent))

    def get_recent_attempts(self, ip: str, minutes: int = 5) -> int:
        """Количество попыток за последние N минут"""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT COUNT(*) as cnt FROM login_attempts
                WHERE ip = ? AND timestamp > datetime('now', ?)
            """, (ip, f"-{minutes} minutes")).fetchone()
            return row["cnt"] if row else 0

    def get_top_attackers(self, limit: int = 20) -> List[Dict]:
        """ТОП атакующих IP"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT ip, COUNT(*) as attempts, country,
                       MAX(timestamp) as last_attempt
                FROM login_attempts
                WHERE success = 0
                GROUP BY ip
                ORDER BY attempts DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_attempts_today(self) -> int:
        """Попытки входа сегодня"""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT COUNT(*) as cnt FROM login_attempts
                WHERE date(timestamp) = date('now') AND success = 0
            """).fetchone()
            return row["cnt"] if row else 0

    # === SYSTEM METRICS ===

    def save_metrics(self, cpu: float, ram: float, disk: float,
                     connections: int, net_in: int, net_out: int):
        """Сохранить метрики системы"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO system_metrics
                (cpu_percent, ram_percent, disk_percent, connections, network_in_bytes, network_out_bytes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cpu, ram, disk, connections, net_in, net_out))

    def get_recent_metrics(self, limit: int = 100) -> List[Dict]:
        """Получить последние метрики"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM system_metrics
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_average_metrics(self, hours: int = 24) -> Dict:
        """Средние метрики за N часов"""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT AVG(cpu_percent) as avg_cpu,
                       AVG(ram_percent) as avg_ram,
                       AVG(disk_percent) as avg_disk,
                       AVG(connections) as avg_conn
                FROM system_metrics
                WHERE timestamp > datetime('now', ?)
            """, (f"-{hours} hours",)).fetchone()
            return dict(row) if row else {}

    # === USER SETTINGS ===

    def get_user_settings(self, telegram_id: int) -> Optional[Dict]:
        """Настройки пользователя"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM user_settings WHERE telegram_id = ?",
                (telegram_id,)
            ).fetchone()
            return dict(row) if row else None

    def save_user_settings(self, telegram_id: int, username: str = None,
                           language: str = "ru"):
        """Сохранить настройки пользователя"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_settings
                (telegram_id, username, language, last_active)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (telegram_id, username, language))

    def get_admin_ids(self) -> List[int]:
        """Получить ID всех админов"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT telegram_id FROM user_settings WHERE role = 'admin'"
            ).fetchall()
            return [r["telegram_id"] for r in rows]

    # === AUDIT LOG ===

    def log_action(self, telegram_id: int, action: str,
                   details: str = None, ip_address: str = None):
        """Записать действие в аудит-лог"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO audit_log (telegram_id, action, details, ip_address)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, action, details, ip_address))

    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        """Получить аудит-лог"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    # === STATISTICS ===

    def get_today_stats(self) -> Dict:
        """Статистика за сегодня"""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
                    COUNT(DISTINCT ip) as unique_ips
                FROM login_attempts
                WHERE date(timestamp) = date('now')
            """).fetchone()
            return dict(row) if row else {}

    def get_weekly_stats(self) -> List[Dict]:
        """Статистика за неделю"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT date(timestamp) as date,
                       COUNT(*) as attempts,
                       COUNT(DISTINCT ip) as unique_ips
                FROM login_attempts
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY date(timestamp)
                ORDER BY date DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def cleanup_old_data(self, days: int = 30):
        """Очистка старых данных"""
        with self._get_conn() as conn:
            conn.execute("""
                DELETE FROM login_attempts
                WHERE timestamp < datetime('now', ?)
            """, (f"-{days} days",))
            conn.execute("""
                DELETE FROM system_metrics
                WHERE timestamp < datetime('now', '-7 days')
            """)
