#!/usr/bin/env python3
"""
Мониторинг логов Marzban - отслеживание попыток входа в реальном времени
"""
import subprocess
import re
import time
import threading
from typing import Callable, Dict, Optional
from datetime import datetime


class LogMonitor:
    """Мониторинг Docker-логов Marzban"""

    # Паттерны для поиска
    PATTERNS = {
        "login_401": re.compile(
            r'INFO:\s+(\d+\.\d+\.\d+\.\d+):\d+\s+-\s+"POST /api/admin/token HTTP/[^"]*" 401'
        ),
        "login_200": re.compile(
            r'INFO:\s+(\d+\.\d+\.\d+\.\d+):\d+\s+-\s+"POST /api/admin/token HTTP/[^"]*" 200'
        ),
        "login_403": re.compile(
            r'INFO:\s+(\d+\.\d+\.\d+\.\d+):\d+\s+-\s+"POST /api/admin/token HTTP/[^"]*" 403'
        ),
        "general_request": re.compile(
            r'INFO:\s+(\d+\.\d+\.\d+\.\d+):\d+\s+-\s+"(GET|POST|PUT|DELETE|PATCH) ([^ ]+) HTTP/[^"]*" (\d{3})'
        ),
        "error": re.compile(
            r'ERROR:.*',
            re.IGNORECASE
        ),
    }

    def __init__(self, container_name: str = "marzban-marzban-1",
                 check_interval: int = 3, panel_name: str = "marzban"):
        self.container_name = container_name
        self.check_interval = check_interval
        self.panel_name = panel_name
        self.running = False
        self._thread = None

        # Callback-и для событий
        self.callbacks: Dict[str, list] = {
            "login_401": [],
            "login_200": [],
            "login_403": [],
            "error": [],
            "request": [],
        }

        self._processed_hashes = set()
        self._max_cache = 10000

    def on(self, event: str, callback: Callable):
        """Регистрация callback на событие"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def _emit(self, event: str, data: Dict):
        """Вызов callback-ов (для использования из потока)"""
        import asyncio
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            pass
        for cb in self.callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    if loop and loop.is_running():
                        asyncio.run_coroutine_threadsafe(cb(data), loop)
            except Exception:
                pass

    def _get_logs(self, lines: int = 50) -> list:
        """Получить последние N строк лога"""
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), self.container_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                output = result.stdout + result.stderr
                return output.splitlines()
        except Exception as e:
            print(f"[LOG-MONITOR] Get logs error: {e}")
        return []

    def _process_line(self, line: str):
        """Обработать строку лога"""
        line_hash = hash(line.strip())
        if line_hash in self._processed_hashes:
            return

        self._processed_hashes.add(line_hash)
        if len(self._processed_hashes) > self._max_cache:
            self._processed_hashes.clear()

        # 401 Unauthorized
        match = self.PATTERNS["login_401"].search(line)
        if match:
            ip = match.group(1)
            self._emit("login_401", {
                "ip": ip,
                "panel": self.panel_name,
                "line": line.strip(),
                "timestamp": datetime.now().isoformat(),
            })
            return

        # 200 OK (успешный вход)
        match = self.PATTERNS["login_200"].search(line)
        if match:
            ip = match.group(1)
            self._emit("login_200", {
                "ip": ip,
                "panel": self.panel_name,
                "line": line.strip(),
                "timestamp": datetime.now().isoformat(),
            })
            return

        # Ошибки
        if self.PATTERNS["error"].search(line):
            self._emit("error", {
                "line": line.strip(),
                "panel": self.panel_name,
                "timestamp": datetime.now().isoformat(),
            })

        # Общий запрос
        match = self.PATTERNS["general_request"].search(line)
        if match:
            self._emit("request", {
                "ip": match.group(1),
                "method": match.group(2),
                "path": match.group(3),
                "status": int(match.group(4)),
                "panel": self.panel_name,
                "timestamp": datetime.now().isoformat(),
            })

    def start(self):
        """Запустить мониторинг"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print(f"[LOG-MONITOR] Started monitoring {self.container_name}")

    def stop(self):
        """Остановить мониторинг"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        print(f"[LOG-MONITOR] Stopped monitoring {self.container_name}")

    def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self.running:
            try:
                lines = self._get_logs(100)
                for line in lines:
                    if line.strip():
                        self._process_line(line)
            except Exception as e:
                print(f"[LOG-MONITOR] Loop error: {e}")

            time.sleep(self.check_interval)


class MultiPanelLogMonitor:
    """Мониторинг нескольких панелей"""

    def __init__(self):
        self.monitors: Dict[str, LogMonitor] = {}

    def add_panel(self, container_name: str, panel_name: str,
                  check_interval: int = 3):
        """Добавить панель для мониторинга"""
        monitor = LogMonitor(container_name, check_interval, panel_name)
        self.monitors[panel_name] = monitor
        return monitor

    def on(self, event: str, callback: Callable):
        """Регистрация callback на все панели"""
        for monitor in self.monitors.values():
            monitor.on(event, callback)

    def start_all(self):
        """Запустить все мониторы"""
        for name, monitor in self.monitors.items():
            monitor.start()

    def stop_all(self):
        """Остановить все мониторы"""
        for name, monitor in self.monitors.items():
            monitor.stop()
