<div align="center">

# 🛡️ SystemFlow

**🇷🇺 Универсальный Telegram-бот для безопасности и мониторинга сервера с Marzban**

**🇬🇧 Universal Telegram Bot for Marzban Server Security & Monitoring**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-yellow.svg)](https://docs.aiogram.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Marzban](https://img.shields.io/badge/Marzban-Compatible-orange.svg)](https://github.com/Gozargah/Marzban)

**[🇷🇺 Русская версия](#-русский)** • **[🇬🇧 English Version](#-english)**

</div>

---

<div align="center">

# 🇷🇺 Русский

</div>

## ✨ Возможности

### 🔐 Безопасность
- **Мониторинг логов** в реальном времени
- **Мгновенные уведомления** о попытках входа (401)
- **Бан IP кнопкой** прямо из уведомления
- **Автобан** после N неудачных попыток
- **GeoIP** — страна, город, провайдер с флагом 🇷🇺🇮🇷🇺🇸
- **WHOIS** информация об IP
- **Временные баны** — 1ч, 24ч или навсегда

### 📊 Мониторинг системы
- CPU, RAM, Disk usage
- Активные соединения
- Сетевой трафик
- ТОП процессов
- Uptime сервера
- **Оповещения** при превышении порогов

### 🐳 Docker
- Статус контейнеров
- Ресурсы контейнеров
- Уведомления о падении/перезапуске
- Перезапуск из бота

### 💬 Telegram
- **Reply-клавиатуры** — все команды кнопками
- **Inline-кнопки** — для действий (бан, инфо)
- **Два языка** — 🇷🇺 Русский и 🇬🇧 English
- **Выбор языка** при первом запуске

### 📈 Отчёты и бэкапы
- Графики CPU/RAM/атак
- Ежедневные отчёты
- Бэкап одной кнопкой
- Отправка файла в чат

## 🚀 Установка

### В одну команду:

```bash
bash <(curl -s https://raw.githubusercontent.com/R3G1ST/SystemFlow/main/install.sh)
```

### Вручную:

```bash
cd /opt && git clone https://github.com/R3G1ST/SystemFlow.git
cd SystemFlow && bash install.sh
```

### Настройка .env

```env
# Токен бота от @BotFather
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Ваш Telegram ID (от @userinfobot)
ADMIN_USER_IDS=123456789

# Язык: ru или en
LANGUAGE=ru
```

## 📋 Команды

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню + выбор языка |
| `/status` | Статус сервера |
| `/banned` | Список забаненных |
| `/unban <ip>` | Разбанить IP |
| `/connections` | Активные соединения |
| `/logs [n]` | Последние N логов |
| `/backup` | Создать бэкап |
| `/help` | Справка |

## 🎯 Как работает

```
Marzban панель → Docker логи → SystemFlow монитор
                                      │
                            Обнаружил 401?
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              GeoIP поиск       Автобан          Уведомление
              Страна + ISP      iptables DROP    в Telegram
                                                      │
                                        [🚫 БАН] [🔍 Инфо] [⏳ Бан 1ч]
```

## 📂 Структура

```
SystemFlow/
├── bot.py              # Главный файл
├── config.py           # Конфигурация
├── database.py         # База данных SQLite
├── i18n.py             # 🆕 Локализация RU/EN
├── monitors/           # Мониторы логов, системы, Docker
├── handlers/           # Хендлеры команд
├── utils/              # Утилиты: iptables, GeoIP, бэкапы, API
├── install.sh          # Установщик
└── .env.example        # Шаблон конфига
```

## 🔧 Управление

```bash
systemctl status marzban-security-bot   # Статус
systemctl restart marzban-security-bot  # Перезапуск
journalctl -u marzban-security-bot -f   # Логи
```

## 📄 Лицензия

MIT — используйте свободно!

---

<div align="center">

# 🇬🇧 English

</div>

## ✨ Features

### 🔐 Security
- **Real-time log monitoring**
- **Instant notifications** on failed login (401)
- **One-click IP ban** from notification
- **AutoBan** after N failed attempts
- **GeoIP** — country, city, ISP with flag 🇷🇺🇮🇷🇺🇸
- **WHOIS** IP information
- **Temporary bans** — 1h, 24h or permanent

### 📊 System Monitoring
- CPU, RAM, Disk usage
- Active connections
- Network traffic
- Top processes
- Server uptime
- **Alerts** when thresholds exceeded

### 🐳 Docker
- Container status
- Container resources
- Crash/restart notifications
- Remote restart from bot

### 💬 Telegram
- **Reply keyboards** — all commands as buttons
- **Inline buttons** — for actions (ban, info)
- **Two languages** — 🇷🇺 Russian and 🇬🇧 English
- **Language selection** on first launch

### 📈 Reports & Backups
- CPU/RAM/attack charts
- Daily reports
- One-click backup
- File delivery to chat

## 🚀 Installation

### One-line install:

```bash
bash <(curl -s https://raw.githubusercontent.com/R3G1ST/SystemFlow/main/install.sh)
```

### Manual:

```bash
cd /opt && git clone https://github.com/R3G1ST/SystemFlow.git
cd SystemFlow && bash install.sh
```

### Configure .env

```env
# Bot token from @BotFather
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Your Telegram ID (from @userinfobot)
ADMIN_USER_IDS=123456789

# Language: ru or en
LANGUAGE=en
```

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/start` | Main menu + language selection |
| `/status` | Server status |
| `/banned` | Banned IPs list |
| `/unban <ip>` | Unban an IP |
| `/connections` | Active connections |
| `/logs [n]` | Last N log lines |
| `/backup` | Create backup |
| `/help` | Help |

## 🎯 How it works

```
Marzban panel → Docker logs → SystemFlow monitor
                                      │
                            Detected 401?
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              GeoIP lookup       AutoBan         Notification
              Country + ISP      iptables DROP   to Telegram
                                                      │
                                        [🚫 BAN] [🔍 Info] [⏳ Ban 1h]
```

## 📂 Structure

```
SystemFlow/
├── bot.py              # Main entry point
├── config.py           # Configuration
├── database.py         # SQLite database
├── i18n.py             # 🆕 Localization RU/EN
├── monitors/           # Log, system, Docker monitors
├── handlers/           # Command handlers
├── utils/              # Utils: iptables, GeoIP, backup, API
├── install.sh          # Installer
└── .env.example        # Config template
```

## 🔧 Management

```bash
systemctl status marzban-security-bot   # Status
systemctl restart marzban-security-bot  # Restart
journalctl -u marzban-security-bot -f   # Logs
```

## 📄 License

MIT — use freely!

---

<div align="center">

**🇷🇺 Сделано с ❤️ для безопасности вашего сервера**

**🇬🇧 Made with ❤️ for your server security**

[⭐ Star this repo](https://github.com/R3G1ST/SystemFlow) if you find it useful!

</div>
