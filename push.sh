#!/bin/bash
# Авто-пуш исправлений на GitHub
# Вызывается после каждого исправления

cd /opt/marzban-security-bot

# Исключаем секреты
git rm --cached .env bot.db bot.db-shm bot.db-wal 2>/dev/null
git add -A
git commit -m "$1"
git push origin main

echo "✅ Запушено: $1"
