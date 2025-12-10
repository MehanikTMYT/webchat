#!/bin/bash

# Скрипт для деплоя на VDS
set -e  # Выход при ошибке

echo "Начинаем деплой на VDS..."

# Проверяем, что мы на нужной машине
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с правами root"
    exit 1
fi

# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
apt install -y python3 python3-pip nginx git curl

# Устанавливаем Python зависимости
pip3 install -r /workspace/requirements.txt

# Копируем конфигурацию Nginx
cp /workspace/nginx/chatbot.conf /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/chatbot.conf /etc/nginx/sites-enabled/

# Проверяем конфигурацию Nginx
nginx -t

# Перезапускаем Nginx
systemctl restart nginx

# Запускаем backend сервер
cd /workspace
nohup python3 -m backend.main > /var/log/chatbot_backend.log 2>&1 &

echo "Деплой завершен!"
echo "Backend запущен на порту $(grep API_GATEWAY_PORT .env.universal | cut -d'=' -f2)"
echo "Nginx настроен на домен: $(grep VDS_DOMAIN .env.universal | cut -d'=' -f2)"