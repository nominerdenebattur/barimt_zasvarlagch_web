#!/bin/bash

# AI Invoice Processing System Installation Script
# Архитектур: WebUI → Linux Service → AI Module → Database

echo "==================================="
echo "AI Invoice System суулгаж байна..."
echo "==================================="

# 1. System dependencies
echo "1. System packages суулгаж байна..."
sudo apt-get update
sudo apt-get install -y redis-server python3-pip python3-dev

# 2. Redis эхлүүлэх
echo "2. Redis сервис эхлүүлж байна..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 3. Python dependencies
echo "3. Python packages суулгаж байна..."
pip3 install -r requirements.txt

# 4. Environment variables тохируулах
echo "4. Environment variables үүсгэж байна..."
cat > .env << EOF
# Redis тохиргоо
REDIS_HOST=localhost
REDIS_PORT=6379

# OpenAI API
OPENAI_API_KEY=your-openai-api-key-here

# Django тохиргоо
DEBUG=False
SECRET_KEY=your-secret-key-here

# Database
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Logging
LOG_LEVEL=INFO
EOF

echo "⚠️  .env файлыг засаарай: nano .env"

# 5. Log директори үүсгэх
echo "5. Log директори үүсгэж байна..."
sudo mkdir -p /var/log/invoice-system
sudo chown $USER:$USER /var/log/invoice-system

# 6. Systemd service суулгах
echo "6. Systemd service бүртгэж байна..."
sudo cp invoice-daemon.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "==================================="
echo "Суулгалт дууслаа!"
echo "==================================="
echo ""
echo "Дараагийн алхамууд:"
echo ""
echo "1. OpenAI API key-г тохируулах:"
echo "   nano .env"
echo ""
echo "2. Django migration хийх:"
echo "   python manage.py makemigrations"
echo "   python manage.py migrate"
echo ""
echo "3. Service эхлүүлэх:"
echo "   sudo systemctl start invoice-daemon"
echo "   sudo systemctl enable invoice-daemon"
echo ""
echo "4. Статус шалгах:"
echo "   sudo systemctl status invoice-daemon"
echo ""
echo "5. Logs харах:"
echo "   sudo journalctl -u invoice-daemon -f"
echo ""
