#!/bin/bash
# ============================================
# Marzban Security Bot v3 - Установка
# Универсальный скрипт для Ubuntu серверов
# ============================================

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Переменные
BOT_DIR="/opt/marzban-security-bot"
BOT_USER="root"
BOT_SERVICE="marzban-security-bot"

echo -e "${BLUE}"
echo "========================================"
echo "  Marzban Security Bot v3 - Installer"
echo "========================================"
echo -e "${NC}"

# Проверка root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Запустите от root${NC}"
    exit 1
fi

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен!${NC}"
    echo "Установите Docker: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Проверка существования папки бота
if [ ! -d "$BOT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Папка бота не найдена в $BOT_DIR${NC}"
    echo "Скачайте бота или скопируйте файлы в $BOT_DIR"
    exit 1
fi

cd "$BOT_DIR"

# 1. Установка зависимостей
echo -e "\n${BLUE}📦 Установка зависимостей...${NC}"
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv whois iptables > /dev/null 2>&1
echo -e "${GREEN}✅ Зависимости установлены${NC}"

# 2. Создание virtualenv
echo -e "\n${BLUE}🐍 Создание virtualenv...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtualenv создан${NC}"
fi

# 3. Установка Python пакетов
echo -e "\n${BLUE}📚 Установка Python пакетов...${NC}"
source venv/bin/activate
pip install -q --upgrade pip

# Создаём requirements.txt если нет
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << 'EOF'
aiogram>=3.0.0
python-dotenv>=1.0.0
requests>=2.31.0
psutil>=5.9.0
matplotlib>=3.7.0
EOF
fi

pip install -q -r requirements.txt
echo -e "${GREEN}✅ Python пакеты установлены${NC}"

# 4. Создание .env если нет
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}⚙️  Создание конфигурации...${NC}"
    cp .env.example .env

    echo -e "${YELLOW}📝 Введите токен бота от @BotFather:${NC}"
    read -p "BOT_TOKEN: " BOT_TOKEN
    sed -i "s/your_bot_token_here/$BOT_TOKEN/" .env

    echo -e "${YELLOW}📝 Введите ваш Telegram ID (получить через @userinfobot):${NC}"
    read -p "ADMIN_USER_IDS: " ADMIN_ID
    sed -i "s/123456789/$ADMIN_ID/" .env

    echo -e "${GREEN}✅ Конфигурация создана${NC}"
else
    echo -e "${GREEN}✅ .env уже существует${NC}"
fi

# 5. Создание директорий
echo -e "\n${BLUE}📁 Создание директорий...${NC}"
mkdir -p backups reports logs
echo -e "${GREEN}✅ Директории созданы${NC}"

# 6. Создание systemd сервиса
echo -e "\n${BLUE}⚙️  Создание systemd сервиса...${NC}"
cat > /etc/systemd/system/${BOT_SERVICE}.service << EOF
[Unit]
Description=Marzban Security Bot v3
After=network-online.target docker.service
Wants=docker.service

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python3 $BOT_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=append:$BOT_DIR/logs/bot.log
StandardError=append:$BOT_DIR/logs/bot-error.log

# Security
NoNewPrivileges=false
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${BOT_SERVICE}
echo -e "${GREEN}✅ Systemd сервис создан${NC}"

# 7. Настройка cron для бэкапов
echo -e "\n${BLUE}⏰ Настройка cron для автобэкапов...${NC}"
(crontab -l 2>/dev/null; echo "0 3 * * * $BOT_DIR/venv/bin/python3 $BOT_DIR/bot.py --backup") | crontab -
echo -e "${GREEN}✅ Cron настроён${NC}"

# 8. Запуск бота
echo -e "\n${BLUE}🚀 Запуск бота...${NC}"
systemctl start ${BOT_SERVICE}
sleep 3

# Проверка статуса
if systemctl is-active --quiet ${BOT_SERVICE}; then
    echo -e "\n${GREEN}========================================"
    echo "  ✅ Бот успешно установлен и запущен!"
    echo "========================================${NC}"
    echo -e "\n📋 Команды:"
    echo "  systemctl status ${BOT_SERVICE}  # Статус"
    echo "  systemctl restart ${BOT_SERVICE} # Перезапуск"
    echo "  journalctl -u ${BOT_SERVICE} -f  # Логи"
    echo ""
    echo -e "💬 Откройте Telegram и найдите вашего бота"
    echo -e "   и отправьте /start для начала работы!"
else
    echo -e "\n${RED}❌ Бот не запустился!${NC}"
    echo "Проверьте логи:"
    echo "  journalctl -u ${BOT_SERVICE} -n 50 --no-pager"
    exit 1
fi

echo -e "\n${GREEN}🛡️ Marzban Security Bot v3 готов к работе!${NC}"
