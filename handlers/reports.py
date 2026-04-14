#!/usr/bin/env python3
"""
Генератор отчётов и графиков: CPU, RAM, атаки, трафик
"""
import os
import matplotlib
matplotlib.use('Agg')  # Без GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import List, Dict
from database import Database


class ReportGenerator:
    """Генерация отчётов и графиков"""

    def __init__(self, db: Database, output_dir: str = "/opt/marzban-security-bot/reports"):
        self.db = db
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_cpu_chart(self, hours: int = 24) -> str:
        """График CPU за N часов"""
        metrics = self.db.get_recent_metrics(100)
        if not metrics:
            return ""

        metrics.reverse()

        times = [datetime.fromisoformat(m["timestamp"]) for m in metrics]
        cpu_values = [m["cpu_percent"] for m in metrics]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(times, cpu_values, color='#ff6b6b', linewidth=2, label='CPU %')
        ax.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='Threshold 80%')
        ax.fill_between(times, cpu_values, alpha=0.3, color='#ff6b6b')

        ax.set_title('CPU Usage', fontsize=16, fontweight='bold')
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('CPU %', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        filename = f"cpu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150)
        plt.close()

        return filepath

    def generate_ram_chart(self, hours: int = 24) -> str:
        """График RAM"""
        metrics = self.db.get_recent_metrics(100)
        if not metrics:
            return ""

        metrics.reverse()

        times = [datetime.fromisoformat(m["timestamp"]) for m in metrics]
        ram_values = [m["ram_percent"] for m in metrics]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(times, ram_values, color='#4ecdc4', linewidth=2, label='RAM %')
        ax.axhline(y=90, color='red', linestyle='--', alpha=0.5, label='Threshold 90%')
        ax.fill_between(times, ram_values, alpha=0.3, color='#4ecdc4')

        ax.set_title('RAM Usage', fontsize=16, fontweight='bold')
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('RAM %', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        filename = f"ram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150)
        plt.close()

        return filepath

    def generate_attacks_chart(self, days: int = 7) -> str:
        """График атак за N дней"""
        stats = self.db.get_weekly_stats()
        if not stats:
            return ""

        stats.reverse()

        dates = [datetime.strptime(s["date"], "%Y-%m-%d") for s in stats]
        attempts = [s["attempts"] for s in stats]
        unique_ips = [s["unique_ips"] for s in stats]

        fig, ax1 = plt.subplots(figsize=(12, 6))

        color = '#ff6b6b'
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Attempts', color=color, fontsize=12)
        ax1.bar(dates, attempts, color=color, alpha=0.6, label='Attempts')
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()
        color = '#4ecdc4'
        ax2.set_ylabel('Unique IPs', color=color, fontsize=12)
        ax2.plot(dates, unique_ips, color=color, linewidth=2, marker='o', label='Unique IPs')
        ax2.tick_params(axis='y', labelcolor=color)

        plt.title(f'Attack Statistics (Last {days} days)', fontsize=16, fontweight='bold')
        fig.tight_layout()

        filename = f"attacks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150)
        plt.close()

        return filepath

    def generate_connections_chart(self) -> str:
        """График соединений"""
        metrics = self.db.get_recent_metrics(100)
        if not metrics:
            return ""

        metrics.reverse()

        times = [datetime.fromisoformat(m["timestamp"]) for m in metrics]
        conn_values = [m["connections"] for m in metrics]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(times, conn_values, color='#ffd93d', linewidth=2, label='Connections')
        ax.fill_between(times, conn_values, alpha=0.3, color='#ffd93d')

        ax.set_title('Active Connections', fontsize=16, fontweight='bold')
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Connections', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        filename = f"connections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150)
        plt.close()

        return filepath

    def generate_daily_report(self) -> str:
        """Текстовый ежедневный отчёт"""
        stats = self.db.get_today_stats()
        avg_metrics = self.db.get_average_metrics(24)
        banned_count = self.db.get_banned_count()
        top_attackers = self.db.get_top_attackers(5)

        text = (
            f"📊 **DAILY REPORT** 📊\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"🔐 **Security:**\n"
            f"• Failed login attempts: **{stats.get('failed', 0)}**\n"
            f"• Successful logins: **{stats.get('success', 0)}**\n"
            f"• Unique attacking IPs: **{stats.get('unique_ips', 0)}**\n"
            f"• Currently banned: **{banned_count}**\n\n"
            f"📈 **System (24h avg):**\n"
            f"• CPU: **{avg_metrics.get('avg_cpu', 0):.1f}%**\n"
            f"• RAM: **{avg_metrics.get('avg_ram', 0):.1f}%**\n"
            f"• Disk: **{avg_metrics.get('avg_disk', 0):.1f}%**\n"
            f"• Connections: **{avg_metrics.get('avg_conn', 0):.0f}**\n"
        )

        if top_attackers:
            text += f"\n🏆 **Top Attackers:**\n"
            for i, attacker in enumerate(top_attackers, 1):
                text += f"{i}. `{attacker['ip']}` - {attacker['attempts']} attempts\n"

        filepath = os.path.join(self.output_dir, f"daily_{datetime.now().strftime('%Y%m%d')}.txt")
        with open(filepath, 'w') as f:
            f.write(text)

        return filepath

    def cleanup_old_reports(self, days: int = 30):
        """Очистка старых отчётов"""
        try:
            for f in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, f)
                if os.path.isfile(filepath):
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if (datetime.now() - mtime).days > days:
                        os.remove(filepath)
        except Exception as e:
            print(f"[REPORTS] Cleanup error: {e}")
