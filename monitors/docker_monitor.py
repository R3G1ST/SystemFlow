#!/usr/bin/env python3
"""
Мониторинг Docker-контейнеров
"""
import subprocess
import json
import threading
import time
from typing import Callable, Dict, List, Optional
from datetime import datetime


class DockerMonitor:
    """Мониторинг Docker контейнеров"""

    def __init__(self, check_interval: int = 30, monitored_containers: list = None):
        self.check_interval = check_interval
        self.running = False
        self._thread = None

        if monitored_containers is None:
            monitored_containers = ["marzban-marzban-1"]
        self.monitored = monitored_containers

        self.callbacks: Dict[str, list] = {
            "container_down": [],
            "container_restart": [],
            "container_logs": [],
            "status_update": [],
        }

    def on(self, event: str, callback: Callable):
        """Регистрация callback"""
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

    def _run_docker(self, args: list) -> Optional[str]:
        """Выполнить docker команду"""
        try:
            result = subprocess.run(
                ["docker"] + args,
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None

    def get_containers_status(self) -> List[Dict]:
        """Статус всех контейнеров"""
        containers = []
        output = self._run_docker(["ps", "--format", "{{.Names}}|{{.Status}}|{{.Image}}"])
        if output:
            for line in output.split("\n"):
                parts = line.split("|")
                if len(parts) >= 2:
                    containers.append({
                        "name": parts[0],
                        "status": parts[1],
                        "image": parts[2] if len(parts) > 2 else "",
                        "running": "Up" in parts[1],
                    })
        return containers

    def is_container_running(self, container: str) -> bool:
        """Проверить, запущен ли контейнер"""
        output = self._run_docker(["ps", "--filter", f"name={container}", "--format", "{{.Names}}"])
        return output is not None and container in output

    def get_container_stats(self, container: str) -> Dict:
        """Статистика контейнера"""
        output = self._run_docker([
            "stats", "--no-stream", "--format",
            "{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.NetIO}}|{{.BlockIO}}",
            container
        ])
        if output:
            parts = output.split("|")
            if len(parts) >= 3:
                return {
                    "cpu": parts[0],
                    "mem_usage": parts[1],
                    "mem_percent": parts[2],
                    "net_io": parts[3] if len(parts) > 3 else "N/A",
                    "block_io": parts[4] if len(parts) > 4 else "N/A",
                }
        return {}

    def get_container_logs(self, container: str, lines: int = 50) -> str:
        """Логи контейнера"""
        output = self._run_docker(["logs", "--tail", str(lines), container])
        return output or ""

    def restart_container(self, container: str) -> bool:
        """Перезапустить контейнер"""
        try:
            result = subprocess.run(
                ["docker", "restart", container],
                capture_output=True, timeout=30
            )
            return result.returncode == 0
        except:
            return False

    def start_container(self, container: str) -> bool:
        """Запустить контейнер"""
        try:
            result = subprocess.run(
                ["docker", "start", container],
                capture_output=True, timeout=30
            )
            return result.returncode == 0
        except:
            return False

    def stop_container(self, container: str) -> bool:
        """Остановить контейнер"""
        try:
            result = subprocess.run(
                ["docker", "stop", container],
                capture_output=True, timeout=30
            )
            return result.returncode == 0
        except:
            return False

    def start(self):
        """Запустить мониторинг"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("[DOCKER-MONITOR] Started")

    def stop(self):
        """Остановить мониторинг"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[DOCKER-MONITOR] Stopped")

    def _monitor_loop(self):
        """Основной цикл"""
        previous_states = {}

        while self.running:
            try:
                containers = self.get_containers_status()
                current_states = {}

                for c in containers:
                    name = c["name"]
                    current_states[name] = c["running"]

                    # Отправляем обновление статуса
                    self._emit("status_update", c)

                    # Проверяем изменения состояния
                    if name in previous_states:
                        if previous_states[name] and not c["running"]:
                            self._emit("container_down", {
                                "name": name,
                                "timestamp": datetime.now().isoformat(),
                            })
                        elif not previous_states[name] and c["running"]:
                            self._emit("container_restart", {
                                "name": name,
                                "timestamp": datetime.now().isoformat(),
                            })

                    # Проверяем monitored контейнеры
                    if name in self.monitored and not c["running"]:
                        self._emit("container_down", {
                            "name": name,
                            "timestamp": datetime.now().isoformat(),
                        })

                previous_states = current_states

            except Exception as e:
                print(f"[DOCKER-MONITOR] Loop error: {e}")

            time.sleep(self.check_interval)
