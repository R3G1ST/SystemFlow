<div align="center">

# 🛡️ SystemFlow

**Universal Telegram Bot for Marzban Server Security & Monitoring**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-yellow.svg)](https://docs.aiogram.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Marzban](https://img.shields.io/badge/Marzban-Compatible-orange.svg)](https://github.com/Gozargah/Marzban)
[![Stars](https://img.shields.io/github/stars/R3G1ST/SystemFlow?style=social)](https://github.com/R3G1ST/SystemFlow/stargazers)

<img src="https://img.shields.io/badge/🔐_Security-Monitoring-red?style=for-the-badge" alt="Security">
<img src="https://img.shields.io/badge/📊_Analytics-Realtime-blue?style=for-the-badge" alt="Analytics">
<img src="https://img.shields.io/badge/🚫_AutoBan-Instant-green?style=for-the-badge" alt="AutoBan">

**One-click install • Multi-panel support • Real-time alerts • GeoIP • Charts**

[🚀 Quick Start](#-installation) • [📖 Documentation](#-features) • [💬 Support](#-support)

</div>

---

## 📸 Screenshots

<details>
<summary><b>Click to see bot screenshots</b></summary>

| Login Alert | Server Status | Ban Action |
|:---:|:---:|:---:|
| 🔔 Real-time 401 notifications | 📊 Full system overview | 🚫 One-click IP ban |
| Country + ISP info | CPU/RAM/Disk + Docker | Permanent or temporary |

</details>

---

## ✨ Features

### 🔐 Security & Protection
- **Real-time log monitoring** — tracks Marzban Docker logs live
- **Instant 401 alerts** — notified on every failed login attempt
- **One-click ban** — block attacker IP directly from notification
- **Smart AutoBan** — automatic ban after N failed attempts (configurable)
- **GeoIP lookup** — country, city, ISP, ASN with flag emoji 🇮🇷🇺🇸🇩🇪
- **WHOIS info** — detailed IP information
- **Temporary bans** — 1h, 24h, or permanent options
- **Whitelist support** — never ban trusted IPs
- **Audit logging** — every action is recorded

### 📊 System Monitoring
- **CPU / RAM / Disk** — real-time resource tracking
- **Active connections** — monitor TCP/UDP connections
- **Network traffic** — bytes sent/received
- **Load Average** — system load metrics
- **Top processes** — highest CPU/RAM consumers
- **Server uptime** — time since last boot
- **Threshold alerts** — notifications when resources exceed limits

### 🐳 Docker Management
- **Container status** — monitor all Marzban containers
- **Resource usage** — CPU/RAM/network per container
- **Crash alerts** — instant notification if container goes down
- **Remote restart** — restart containers from Telegram
- **Auto-discovery** — finds Marzban panels automatically

### 👥 Marzban User Management
- **User list** — view all subscribers with traffic stats
- **Status tracking** — active, disabled, limited, expired
- **Traffic monitoring** — used vs limit with progress
- **Expiry alerts** — notifications for expiring subscriptions
- **Reset traffic** — reset user data usage
- **Disable users** — block access from bot
- **Create users** — add new subscribers (coming soon)

### 📈 Reports & Analytics
- **CPU/RAM charts** — beautiful PNG graphs
- **Attack statistics** — daily/weekly attack charts
- **Connection trends** — visualize connection patterns
- **Daily reports** — automated summary every day
- **Weekly analytics** — 7-day overview with trends
- **Top attackers** — leaderboard of attacking IPs

### 💾 Backup & Recovery
- **One-click backup** — create Marzban backup from bot
- **Auto-backup** — scheduled backups via cron
- **File delivery** — sends backup file to Telegram
- **Backup history** — list all backups with size/date

### 🌍 Multi-Panel & Multi-Server
- **Auto-discovery** — finds all Marzban Docker containers
- **Multi-panel mode** — monitor multiple panels simultaneously
- **Universal installer** — works on any Ubuntu server
- **Configurable** — `.env` file for all settings

---

## 🚀 Installation

### One-Line Install (Recommended)

```bash
bash <(curl -s https://raw.githubusercontent.com/R3G1ST/SystemFlow/main/install.sh)
```

### Manual Install

```bash
# 1. Clone repository
cd /opt
git clone https://github.com/R3G1ST/SystemFlow.git
cd SystemFlow

# 2. Run installer
bash install.sh
```

### Docker Install (Coming Soon)

```bash
docker run -d \
  --name systemflow \
  --network host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/.env:/app/.env \
  r3g1st/systemflow:latest
```

---

## ⚙️ Configuration

Create `.env` file (installer does this automatically):

```env
# ─── Telegram Bot ─────────────────────────
# Get token from @BotFather
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Your Telegram ID (get from @userinfobot)
# Multiple admins: 123456789,987654321
ADMIN_USER_IDS=123456789

# ─── Security ──────────────────────────────
# Auto-ban after N failed attempts
MAX_LOGIN_ATTEMPTS=3
BAN_TIME_WINDOW=300        # 5 minutes window
AUTOBAN_ENABLED=true

# ─── Notifications ─────────────────────────
NOTIFY_ON_401=true         # Failed login alerts
NOTIFY_ON_BAN=true         # Ban confirmations
NOTIFY_ON_HIGH_CPU=true    # CPU threshold alerts
NOTIFY_ON_HIGH_RAM=true    # RAM threshold alerts
CPU_THRESHOLD=80           # Percent
RAM_THRESHOLD=90           # Percent
CONNECTIONS_THRESHOLD=500  # Max connections

# ─── Monitoring ────────────────────────────
MONITOR_INTERVAL=3         # Log check interval (seconds)
SYSTEM_CHECK_INTERVAL=30   # System metrics interval

# ─── Multi-Panel (optional) ────────────────
# Format: container_name:URL,container2:URL2
# MULTI_PANELS=marzban-marzban-1:https://panel1.com,marzban2:https://panel2.com

# ─── Language ──────────────────────────────
# Supported: ru, en, fa
LANGUAGE=ru

# ─── Debug ─────────────────────────────────
DRY_RUN=false   # Test mode (no actual bans)
VERBOSE=false   # Detailed logging
```

---

## 📋 Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Main menu with keyboard | — |
| `/status` | Full server status | — |
| `/security` | Security menu | — |
| `/users` | Marzban users list | — |
| `/docker` | Docker containers | — |
| `/backup` | Create Marzban backup | — |
| `/banned` | Show banned IPs list | — |
| `/unban` | Unban an IP | `/unban 1.2.3.4` |
| `/logs` | View recent logs | `/logs 50` |
| `/connections` | Active connections | — |
| `/reports` | Generate reports | — |
| `/help` | Command reference | — |

---

## 🎯 How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR SERVER                          │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │   Marzban    │───▶│  Docker Logs │                  │
│  │   Panel      │    │  (stdout)    │                  │
│  └──────────────┘    └──────┬───────┘                  │
│                             │                           │
│                    ┌────────▼────────┐                  │
│                    │  SystemFlow     │                  │
│                    │  Bot Monitor    │                  │
│                    │                 │                  │
│                    │  • Parse logs   │                  │
│                    │  • Detect 401   │                  │
│                    │  • GeoIP lookup │                  │
│                    │  • AutoBan      │                  │
│                    │  • System check │                  │
│                    └────────┬────────┘                  │
│                             │                           │
│                    ┌────────▼────────┐                  │
│                    │   iptables      │                  │
│                    │   DROP attacker │                  │
│                    └─────────────────┘                  │
└─────────────────────────┬───────────────────────────────┘
                          │ Telegram API
                          ▼
              ┌───────────────────────┐
              │   YOUR TELEGRAM       │
              │                       │
              │  🔔 Attack detected!  │
              │  🌐 IP: 2.26.125.109  │
              │  🇮🇷 Iran, Tehran     │
              │                       │
              │  [🚫 BAN] [🔍 Info]   │
              └───────────────────────┘
```

---

## 📂 Project Structure

```
SystemFlow/
├── 📄 bot.py                    # Main bot entry point
├── 📄 config.py                 # Configuration + auto-discovery
├── 📄 database.py               # SQLite database layer
├── 📄 requirements.txt          # Python dependencies
├── 📄 install.sh                # Universal installer
├── 📄 .env.example              # Configuration template
├── 📄 LICENSE                   # MIT License
│
├── 📁 monitors/
│   ├── 📄 log_monitor.py        # Docker log monitoring
│   ├── 📄 system_monitor.py     # CPU/RAM/Disk monitoring
│   └── 📄 docker_monitor.py     # Container status monitoring
│
├── 📁 handlers/
│   ├── 📄 admin.py              # Admin commands (/status, etc.)
│   ├── 📄 security.py           # Ban/unban, auto-ban
│   ├── 📄 users.py              # Marzban user management
│   └── 📄 reports.py            # Charts and report generation
│
└── 📁 utils/
    └── 📄 __init__.py           # iptables, GeoIP, backup, API
```

---

## 🔧 Management

```bash
# Check status
systemctl status marzban-security-bot

# Restart bot
systemctl restart marzban-security-bot

# View live logs
journalctl -u marzban-security-bot -f

# View today's logs
journalctl -u marzban-security-bot --since today --no-pager

# Stop bot
systemctl stop marzban-security-bot

# Update bot
cd /opt/SystemFlow && git pull && systemctl restart marzban-security-bot
```

---

## 🛡️ Security Features Deep Dive

### AutoBan Algorithm
1. Monitor Docker logs every 3 seconds
2. Detect `401 Unauthorized` responses from Marzban API
3. Track attempts per IP in 5-minute windows
4. After 3 failed attempts → automatic iptables ban
5. Send confirmation to all admins
6. Rules saved to survive reboots

### GeoIP Integration
- Uses free `ip-api.com` (no API key needed)
- Returns: country, city, ISP, ASN, coordinates
- Flag emoji auto-generated from country code
- Cached to minimize API calls

### Rate Limiting
- Log polling: configurable (default 3s)
- System metrics: configurable (default 30s)
- Docker status: every 30s
- Database cleanup: automatic (30 days)

---

## 📊 Example Notifications

<details>
<summary><b>Failed Login Alert</b></summary>

```
🚨 Failed Login Attempt

🌐 IP: 2.26.125.109 🇮🇷
🌍 Country: Iran - Tehran
🏢 ISP: Telecommunication Company
🖥️ Panel: marzban-marzban-1
🕐 Time: 2026-04-14T05:15:30

⚠️ Попыток за последний час: 3

[🚫 BAN 2.26.125.109] [🔍 Info] [⏳ Ban 1h] [⏳ Ban 24h]
```
</details>

<details>
<summary><b>Server Status</b></summary>

```
📊 Server Status

🟢 CPU: 25.3%
🟢 RAM: 45.2% (452.1 MB / 961.5 MB)
💾 Disk: 62.1% (31.2 GB / 50.0 GB)
🔌 Connections: 234
⏱️ Uptime: 8д 19ч 15м

🐳 Docker Containers:
✅ marzban-marzban-1

🛡️ Security:
🚫 Banned IPs: 47
🔐 Failed attempts today: 156

🔝 Top Processes:
• xray - CPU: 12.3%, RAM: 4.5%
• python - CPU: 5.1%, RAM: 6.5%
• dockerd - CPU: 2.0%, RAM: 2.1%
```
</details>

<details>
<summary><b>Container Down Alert</b></summary>

```
🔴 Container Down!

🐳 Container: marzban-marzban-1
⚠️ Status: STOPPED
🕐 Time: 2026-04-14T12:30:00

[🔄 Restart]
```
</details>

---

## 🌍 Supported Languages

- 🇷🇺 **Russian** (default)
- 🇬🇧 **English** (set `LANGUAGE=en`)
- 🇮🇷 **Persian/Farsi** (set `LANGUAGE=fa`)

---

## 🔌 API Integration

### Marzban API
SystemFlow uses Marzban's REST API for:
- User management (list, disable, reset)
- System statistics
- Inbound configuration
- Subscription links

To enable full features, set API token in `.env`:
```env
MARZBAN_API_TOKEN_MARZBAN_MARBAN_1=your_token_here
```

### External Services
- **ip-api.com** — GeoIP lookup (free, no key)
- **iptables** — IP blocking (built-in)
- **Docker** — Container management (required)

---

## 📝 Changelog

### v3.0.0 (2026-04-14)
- 🎉 Initial release
- 🔐 Real-time log monitoring
- 🚫 AutoBan with inline buttons
- 📊 System monitoring
- 🐳 Docker container monitoring
- 👥 Marzban user management
- 📈 Charts and reports
- 💾 Backup functionality
- 🌍 GeoIP + WHOIS
- 📋 Audit logging
- 🔧 Universal installer

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

- **[aiogram](https://github.com/aiogram/aiogram)** — Telegram Bot framework
- **[Marzban](https://github.com/Gozargah/Marzban)** — Subscription management
- **[psutil](https://github.com/giampaolo/psutil)** — System monitoring
- **[matplotlib](https://matplotlib.org/)** — Chart generation
- **[ip-api.com](https://ip-api.com/)** — GeoIP service

---

## 💬 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/R3G1ST/SystemFlow/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/R3G1ST/SystemFlow/discussions)
- 📧 **Contact**: [R3G1ST](https://github.com/R3G1ST)

---

<div align="center">

**Made with ❤️ for server security**

[⭐ Star this repo](https://github.com/R3G1ST/SystemFlow) if you find it useful!

</div>
