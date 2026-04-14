#!/usr/bin/env python3
"""
Мониторинг системы: CPU, RAM, диск, сеть, соединения
"""
import subprocess
import threading
import time
import psutil
from typing import Callable, Dict
from datetime import datetime


class SystemMonitor:
    """Мониторинг ресурсов сервера"""

    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.running = False
        self._thread = None

        self.callbacks: Dict[str, list] = {
            "high_cpu": [],
            "high_ram": [],
            "high_disk": [],
            "high_connections": [],
            "metrics_update": [],
        }

        # Пороги
        self.cpu_threshold = 80
        self.ram_threshold = 90
        self.disk_threshold = 90
        self.connections_threshold = 500

        # Текущие метрики
        self.current_metrics = {}

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
            except Exception as e:
                pass  # Тихо игнорируем ошибки в потоках

    def _get_cpu(self) -> float:
        """Нагрузка CPU"""
        return psutil.cpu_percent(interval=1)

    def _get_ram(self) -> Dict:
        """Использование RAM"""
        mem = psutil.virtual_memory()
        return {
            "percent": mem.percent,
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
        }

    def _get_disk(self) -> Dict:
        """Использование диска"""
        disk = psutil.disk_usage("/")
        return {
            "percent": disk.percent,
            "total": disk.total,
            "free": disk.free,
            "used": disk.used,
        }

    def _get_connections(self) -> int:
        """Количество TCP соединений"""
        try:
            conns = psutil.net_connections(kind='inet')
            return len([c for c in conns if c.status == 'ESTABLISHED'])
        except:
            # Fallback через ss
            try:
                result = subprocess.run(
                    ["ss", "-t", "-n", "state", "established"],
                    capture_output=True, text=True, timeout=5
                )
                return len(result.stdout.strip().split("\n")) - 1
            except:
                return 0

    def _get_network_io(self) -> Dict:
        """Сетевой трафик"""
        try:
            io = psutil.net_io_counters()
            return {
                "bytes_sent": io.bytes_sent,
                "bytes_recv": io.bytes_recv,
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv,
            }
        except:
            return {"bytes_sent": 0, "bytes_recv": 0}

    def _get_load_average(self) -> Dict:
        """Load Average"""
        try:
            load1, load5, load15 = psutil.getloadavg()
            return {
                "load1": load1,
                "load5": load5,
                "load15": load15,
            }
        except:
            return {"load1": 0, "load5": 0, "load15": 0}

    def _get_top_processes(self, limit: int = 5) -> list:
        """ТОП процессов по CPU"""
        procs = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    if info['cpu_percent'] and info['cpu_percent'] > 0:
                        procs.append({
                            "pid": info['pid'],
                            "name": info['name'],
                            "cpu": info['cpu_percent'],
                            "mem": info['memory_percent'] or 0,
                        })
                except:
                    pass
            procs.sort(key=lambda x: x["cpu"], reverse=True)
            return procs[:limit]
        except:
            return []

    def _get_uptime(self) -> str:
        """Время работы сервера"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        now = datetime.now()
        delta = now - boot_time
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{days}д {hours}ч {minutes}м"

    def get_full_status(self) -> Dict:
        """Полный статус системы"""
        cpu = self._get_cpu()
        ram = self._get_ram()
        disk = self._get_disk()
        connections = self._get_connections()
        network = self._get_network_io()
        load = self._get_load_average()
        top_procs = self._get_top_processes()
        uptime = self._get_uptime()

        return {
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "connections": connections,
            "network": network,
            "load": load,
            "top_processes": top_procs,
            "uptime": uptime,
            "timestamp": datetime.now().isoformat(),
        }

    def start(self):
        """Запустить мониторинг"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("[SYS-MONITOR] Started")

    def stop(self):
        """Остановить мониторинг"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[SYS-MONITOR] Stopped")

    def _monitor_loop(self):
        """Основной цикл"""
        while self.running:
            try:
                cpu = self._get_cpu()
                ram = self._get_ram()
                disk = self._get_disk()
                connections = self._get_connections()
                network = self._get_network_io()

                self.current_metrics = {
                    "cpu": cpu,
                    "ram": ram,
                    "disk": disk,
                    "connections": connections,
                    "network": network,
                    "timestamp": datetime.now().isoformat(),
                }

                # Эмитим обновление метрик
                self._emit("metrics_update", self.current_metrics)

                # Проверка порогов
                if cpu > self.cpu_threshold:
                    self._emit("high_cpu", {
                        "cpu": cpu,
                        "threshold": self.cpu_threshold,
                        "timestamp": datetime.now().isoformat(),
                    })

                if ram["percent"] > self.ram_threshold:
                    self._emit("high_ram", {
                        "ram": ram["percent"],
                        "threshold": self.ram_threshold,
                        "timestamp": datetime.now().isoformat(),
                    })

                if disk["percent"] > self.disk_threshold:
                    self._emit("high_disk", {
                        "disk": disk["percent"],
                        "threshold": self.disk_threshold,
                        "timestamp": datetime.now().isoformat(),
                    })

                if connections > self.connections_threshold:
                    self._emit("high_connections", {
                        "connections": connections,
                        "threshold": self.connections_threshold,
                        "timestamp": datetime.now().isoformat(),
                    })

            except Exception as e:
                print(f"[SYS-MONITOR] Loop error: {e}")

            time.sleep(self.check_interval)
