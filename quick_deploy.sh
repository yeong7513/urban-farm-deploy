#!/bin/bash
# Urban Farm 초간단 배포 스크립트 (50자 제한용)

echo "🚀 Urban Farm 배포 시작..."

# 패키지 설치
apt update -y
apt install -y python3 python3-pip python3-venv mysql-server nginx supervisor

# 프로젝트 생성
mkdir -p /home/urbanfarm
cd /home/urbanfarm

# 최소 requirements.txt
echo "Flask==2.3.3
Flask-SQLAlchemy==3.0.5
PyMySQL==1.1.0
gunicorn==21.2.0" > requirements.txt

# 최소 app.py
echo 'import pymysql
from flask import Flask
pymysql.install_as_MySQLdb()
app = Flask(__name__)
app.config["SECRET_KEY"] = "urbanfarm2024"

@app.route("/")
def index():
    return """
<h1 style="text-align:center;color:#2d5a2d">🌱 Urban Farm</h1>
<p style="text-align:center;font-size:18px">배포 성공!</p>
<div style="max-width:600px;margin:0 auto;padding:20px">
<div style="background:#e8f5e8;padding:20px;margin:10px;border-radius:8px">
<h3>🏡 커뮤니티</h3><p>도시 농업 정보 공유</p></div>
<div style="background:#e8f5e8;padding:20px;margin:10px;border-radius:8px">
<h3>📖 재배 일지</h3><p>작물 재배 과정 기록</p></div>
<div style="background:#e8f5e8;padding:20px;margin:10px;border-radius:8px">
<h3>🤝 나눔 장터</h3><p>수확물 이웃 나눔</p></div>
</div>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)' > app.py

# MySQL 설정
systemctl start mysql
systemctl enable mysql

# Python 환경
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Supervisor 설정
echo '[program:urbanfarm]
command=/home/urbanfarm/venv/bin/gunicorn --bind 127.0.0.1:5000 app:app
directory=/home/urbanfarm
autostart=true
autorestart=true
stdout_logfile=/var/log/urbanfarm.log' > /etc/supervisor/conf.d/urbanfarm.conf

# Nginx 설정
echo 'server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
    }
}' > /etc/nginx/sites-available/urbanfarm

ln -sf /etc/nginx/sites-available/urbanfarm /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 권한 및 서비스 시작
chown -R www-data:www-data /home/urbanfarm
supervisorctl reread
supervisorctl update
supervisorctl start urbanfarm
nginx -t && systemctl restart nginx

echo "🎉 배포 완료! http://192.168.0.27"
supervisorctl status urbanfarm 