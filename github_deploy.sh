#!/bin/bash
# Urban Farm GitHub 자동 배포 스크립트

echo "🚀 Urban Farm GitHub 배포 시작..."

# 패키지 설치
echo "📦 시스템 패키지 설치 중..."
apt update -y
apt install -y python3 python3-pip python3-venv mysql-server nginx supervisor git unzip curl

# GitHub에서 프로젝트 다운로드
echo "📥 GitHub에서 프로젝트 다운로드 중..."
cd /home
rm -rf urbanfarm
git clone https://github.com/yeong7513/urban-farm-deploy.git urbanfarm
# 또는 ZIP 다운로드 방식:
# curl -L https://github.com/yeong7513/urban-farm-deploy/archive/master.zip -o urbanfarm.zip
# unzip urbanfarm.zip
# mv urban-farm-deploy-master urbanfarm

cd /home/urbanfarm

# MySQL 설정
echo "🗄️ MySQL 설정 중..."
systemctl start mysql
systemctl enable mysql

mysql -u root << 'MYSQL_SCRIPT'
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'rootpassword123';
CREATE DATABASE IF NOT EXISTS urbanfarm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'urbanfarm'@'localhost' IDENTIFIED BY 'urbanfarm123';
GRANT ALL PRIVILEGES ON urbanfarm_db.* TO 'urbanfarm'@'localhost';
FLUSH PRIVILEGES;
MYSQL_SCRIPT

# Python 환경 설정
echo "🐍 Python 환경 설정 중..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 데이터베이스 초기화
echo "🗃️ 데이터베이스 초기화 중..."
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database initialized!')
"

# Supervisor 설정
echo "🔧 Supervisor 설정 중..."
cat > /etc/supervisor/conf.d/urbanfarm.conf << 'SUPERVISOR_CONF'
[program:urbanfarm]
command=/home/urbanfarm/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 app:app
directory=/home/urbanfarm
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/urbanfarm.log
SUPERVISOR_CONF

# Nginx 설정
echo "🌐 Nginx 설정 중..."
cat > /etc/nginx/sites-available/urbanfarm << 'NGINX_CONF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/urbanfarm/static;
        expires 30d;
    }
}
NGINX_CONF

ln -sf /etc/nginx/sites-available/urbanfarm /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 권한 설정 및 서비스 시작
echo "🔄 서비스 시작 중..."
chown -R www-data:www-data /home/urbanfarm
chmod -R 755 /home/urbanfarm

supervisorctl reread
supervisorctl update
supervisorctl start urbanfarm

nginx -t && systemctl restart nginx
systemctl enable nginx

# 완료 메시지
echo ""
echo "🎉 =================================="
echo "✅ Urban Farm 배포가 완료되었습니다!"
echo "🌐 웹사이트: http://$(hostname -I | awk '{print $1}')"
echo "📊 상태 확인: supervisorctl status urbanfarm"
echo "📝 로그 확인: tail -f /var/log/urbanfarm.log"
echo "===================================="
echo ""

supervisorctl status urbanfarm 