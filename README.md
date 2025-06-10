# 🌱 Urban Farm - 친환경 도시 농업 플랫폼

도시 거주자들이 농작물을 재배하고, 수확물을 공유하며, 관련 지식을 교류할 수 있는 온라인 커뮤니티 플랫폼입니다.

## 🚀 한 줄 자동 배포

가비아 클라우드 서버 웹 콘솔에서 다음 명령어 하나만 실행하면 됩니다:

```bash
curl -sSL https://raw.githubusercontent.com/yeong7513/urban-farm-deploy/master/github_deploy.sh | bash
```

## ✨ 배포 완료 후

- 🌐 **웹사이트**: `http://서버IP주소`
- 📊 **상태 확인**: `supervisorctl status urbanfarm`
- 📝 **로그 확인**: `tail -f /var/log/urbanfarm.log`
- 🔄 **서비스 재시작**: `sudo supervisorctl restart urbanfarm`

## 🛠️ 포함된 기능

### ✅ 현재 구현된 기능
- **사용자 인증**: 이메일 기반 회원가입/로그인
- **커뮤니티**: 게시글 작성, 조회, 검색, 댓글, 좋아요
- **반응형 디자인**: 모바일/태블릿/데스크톱 최적화
- **실시간 인터랙션**: HTMX 기반 동적 기능

### 🚧 개발 예정 기능
- **재배 일지**: 작물별 재배 기록 및 사진 업로드
- **나눔 장터**: 수확물 나눔 및 지역 기반 매칭
- **교육 콘텐츠**: 작물별 재배 가이드 및 전문가 칼럼

## 🏗️ 기술 스택

- **Backend**: Flask (Python), SQLAlchemy, MySQL
- **Frontend**: HTML5, Tailwind CSS, HTMX, Alpine.js
- **Server**: Nginx (Reverse Proxy), Gunicorn (WSGI)
- **Process Manager**: Supervisor
- **Database**: MySQL 8.0

## 📋 시스템 요구사항

- **OS**: Ubuntu 18.04 이상
- **RAM**: 1GB 이상
- **Storage**: 10GB 이상
- **Network**: 인터넷 연결 필요

## 🔧 수동 설정 (필요시)

### 서비스 관리
```bash
# 서비스 상태 확인
sudo supervisorctl status urbanfarm
sudo systemctl status nginx

# 서비스 재시작
sudo supervisorctl restart urbanfarm
sudo systemctl restart nginx

# 로그 확인
tail -f /var/log/urbanfarm.log
tail -f /var/log/nginx/error.log
```

### 데이터베이스 접속
```bash
mysql -u urbanfarm -p urbanfarm_db
# 비밀번호: urbanfarm123
```

## 🎨 디자인 시스템

### 컬러 팔레트
- **메인**: `#4CAF50` (Urban Green)
- **서브**: `#8BC34A` (Light Green)  
- **액센트**: `#FFC107` (Yellow), `#A1887F` (Brown)
- **배경**: `#F9F9F9` (Light Gray)

### 주요 컴포넌트
- 반응형 네비게이션 바
- 카드형 콘텐츠 레이아웃
- 인터랙티브 버튼 및 폼
- 모바일 친화적 UI

## 📁 프로젝트 구조

```
urban-farm/
├── app.py                 # 메인 Flask 애플리케이션
├── requirements.txt       # Python 의존성
├── github_deploy.sh       # GitHub 자동 배포 스크립트
├── quick_deploy.sh        # 간단 배포 스크립트
├── .gitignore            # Git 무시 파일 목록
├── README.md             # 프로젝트 문서
├── static/               # 정적 파일 (CSS, JS, 이미지)
└── templates/            # HTML 템플릿
    ├── base.html         # 기본 레이아웃
    ├── index.html        # 메인 페이지
    ├── auth/             # 인증 관련 템플릿
    └── community/        # 커뮤니티 템플릿
```

## 🚀 로컬 개발 환경 설정

### 1. 저장소 클론
```bash
git clone https://github.com/yeong7513/urban-farm-deploy.git
cd urban-farm-deploy
```

### 2. 가상환경 생성
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 애플리케이션 실행
```bash
python app.py
```

### 5. 브라우저 접속
```
http://localhost:5000
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이나 제안이 있으시면 언제든지 연락해주세요.

---

**🌱 Urban Farm과 함께 도시에서 시작하는 친환경 농업을 경험해보세요!** 

[program:urbanfarm]
command=/home/urbanfarm/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
directory=/home/urbanfarm
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/urbanfarm.log
environment=DATABASE_URL="mysql://urbanfarm:urbanfarm123@localhost/urbanfarm_db" 