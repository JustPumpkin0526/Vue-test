# VSS (Video Summarization System)

동영상 요약 및 검색 시스템 - AI 기반 동영상 분석 플랫폼

## 📋 목차

- [시스템 요구사항](#시스템-요구사항)
- [프로젝트 구조](#프로젝트-구조)
- [설치 방법](#설치-방법)
- [환경 변수 설정](#환경-변수-설정)
- [데이터베이스 설정](#데이터베이스-설정)
- [실행 방법](#실행-방법)
- [주요 기능](#주요-기능)
- [API 엔드포인트](#api-엔드포인트)
- [문제 해결](#문제-해결)

## 🔧 시스템 요구사항

### 프론트엔드
- **Node.js**: v22.19.0 이상
- **npm**: v10.9.3 이상
- **Vue**: 3.5.21

### 백엔드
- **Python**: 3.8 이상
- **MariaDB**: 10.x 이상 (또는 MySQL 8.x)
- **FFmpeg**: MoviePy 의존성 (비디오 처리용)

### 외부 서비스
- **VIA 서버**: 동영상 분석 서버 (기본: http://172.16.7.64:8101)
- **Ollama**: LLM 서버 (선택사항, 프롬프트 생성 및 번역용)

## 📁 프로젝트 구조

```
VSS_Project/
├── src/
│   ├── api/
│   │   └── vss-api.py          # FastAPI 백엔드 서버
│   ├── components/              # Vue 컴포넌트
│   │   ├── Login.vue           # 로그인
│   │   ├── Register.vue        # 회원가입
│   │   ├── Summarize.vue       # 동영상 요약
│   │   ├── Search.vue          # 동영상 검색
│   │   ├── Report.vue          # 보고서 관리
│   │   └── ...
│   ├── config/
│   │   └── api.js              # API 설정
│   ├── router/
│   │   └── index.js            # Vue Router 설정
│   └── stores/                 # Pinia 상태 관리
├── sql/                        # 데이터베이스 스키마
├── requirements.txt            # Python 의존성
├── package.json               # Node.js 의존성
└── .env                       # 환경 변수 (생성 필요)
```

## 🚀 설치 방법

### 1. 프론트엔드 설치

```bash
# 프로젝트 루트 디렉토리로 이동
cd VSS_Project

# Node.js 의존성 설치
npm install

# Tailwind CSS 설치 (이미 설치되어 있으면 생략)
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p
```

### 2. 백엔드 설치

```bash
# Python 가상 환경 생성 (권장)
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Python 의존성 설치
pip install -r requirements.txt
```

### 3. MoviePy 의존성 설치

**Windows:**
- ImageMagick 설치 (선택사항): https://imagemagick.org/script/download.php

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg imagemagick
```

**macOS:**
```bash
brew install ffmpeg imagemagick
```

## ⚙️ 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# API Base URL (프론트엔드에서 사용)
VITE_API_BASE_URL=http://172.16.15.69:8001

# 백엔드 API 설정 (vss-api.py에서 사용)
API_BASE_URL=http://172.16.15.69:8001

# Ollama 설정 (선택사항)
OLLAMA_BASE_URL=http://172.16.15.69:11434
OLLAMA_MODEL=llama3

# SMTP 설정 (이메일 인증용, 선택사항)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

**참고:** 
- SMTP 설정은 `SMTP_SETUP_GUIDE.md` 참고
- `setup_smtp.py` 스크립트로 자동 설정 가능: `python setup_smtp.py`

## 🗄️ 데이터베이스 설정

### 1. MariaDB 설치 및 실행

MariaDB 서버가 설치되어 있어야 합니다.

### 2. 데이터베이스 및 테이블 생성

```sql
-- 데이터베이스 생성
CREATE DATABASE vss CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 테이블 생성 (sql/ 디렉토리의 SQL 파일 실행)
-- sql/create_vss_user_table.sql
-- sql/create_vss_videos_table.sql
-- sql/create_vss_summaries_table.sql
```

### 3. 데이터베이스 연결 설정

`src/api/vss-api.py` 파일에서 데이터베이스 연결 정보를 수정하세요:

```python
# 데이터베이스 연결 정보 (1492-1496줄)
DB_HOST = "172.16.15.69"      # MariaDB 서버 IP
DB_USER = "root"              # 데이터베이스 사용자
DB_PASSWORD = "pass0001!"     # 비밀번호
DB_PORT = 3306                # 포트
DB_NAME = "vss"               # 데이터베이스 이름
```

### 4. 외부 접속 허용 (필요한 경우)

**MariaDB 서버 설정:**
```sql
-- 원격 접속 허용
GRANT ALL PRIVILEGES ON vss.* TO 'root'@'%' IDENTIFIED BY 'pass0001!';
FLUSH PRIVILEGES;
```

**MariaDB 설정 파일 (`/etc/mysql/mariadb.conf.d/50-server.cnf`):**
```ini
bind-address = 0.0.0.0  # 모든 IP에서 접속 허용
```

## ▶️ 실행 방법

### 1. 백엔드 서버 실행

```bash
# src/api 디렉토리로 이동
cd src/api

# 개발 모드 (외부 접속 허용)
uvicorn vss-api:app --reload --host 0.0.0.0 --port 8001

# 프로덕션 모드
uvicorn vss-api:app --host 0.0.0.0 --port 8001
```

**중요:** 외부 접속을 허용하려면 `--host 0.0.0.0` 옵션이 필요합니다.

### 2. 프론트엔드 서버 실행

```bash
# 프로젝트 루트 디렉토리에서
npm run dev
```

기본적으로 `http://localhost:3000`에서 실행됩니다.

### 3. 외부 접속 설정 (Vite)

`vite.config.js`에서 이미 `host: true`로 설정되어 있어 네트워크를 통해 접속 가능합니다.

## 🎯 주요 기능

### 1. 사용자 관리
- 회원가입 (이메일 인증)
- 로그인/로그아웃
- 비밀번호 재설정
- 프로필 이미지 업로드

### 2. 동영상 관리
- 동영상 업로드
- 동영상 목록 조회
- 동영상 삭제
- 동영상 메타데이터 추출

### 3. 동영상 요약
- AI 기반 동영상 요약 생성
- 사용자 프롬프트 기반 요약
- 요약 결과 저장 및 조회

### 4. 동영상 검색
- 장면 검색 (클립 생성)
- 타임스탬프 추출
- 검색 결과 클립 재생

### 5. 보고서 관리
- 요약 결과를 보고서로 저장
- 보고서 목록 조회
- 보고서 삭제

## 📡 API 엔드포인트

### 인증
- `POST /login` - 로그인
- `POST /register` - 회원가입
- `POST /send-verification-code` - 이메일 인증 코드 전송
- `POST /verify-email-code` - 이메일 인증 코드 검증
- `POST /reset-password` - 비밀번호 재설정

### 동영상
- `POST /upload-video` - 동영상 업로드
- `GET /videos` - 동영상 목록 조회
- `DELETE /videos/{video_id}` - 동영상 삭제
- `GET /convert-video/{video_id}` - 동영상 변환 (AVI → MP4)

### 요약
- `POST /vss-summarize` - 동영상 요약 생성
- `GET /summaries/{video_id}` - 요약 결과 조회
- `DELETE /summaries` - 요약 결과 삭제

### 검색
- `POST /generate-clips` - 장면 검색 및 클립 생성
- `POST /vss-query` - 동영상 질의

### 보고서
- `POST /reports` - 보고서 생성
- `GET /reports` - 보고서 목록 조회
- `GET /reports/{report_id}` - 보고서 상세 조회
- `DELETE /reports/{report_id}` - 보고서 삭제

### 기타
- `GET /via-files` - VIA 서버 파일 목록 조회
- `POST /delete-clips` - 클립 삭제
- `GET /docs` - API 문서 (Swagger UI)

## 🔍 문제 해결

### 백엔드 서버 접속 불가

**문제:** 외부에서 백엔드 서버에 접속할 수 없음

**해결:**
```bash
# --host 0.0.0.0 옵션 추가
uvicorn vss-api:app --reload --host 0.0.0.0 --port 8001
```

**방화벽 설정:**
```powershell
# Windows PowerShell (관리자 권한)
New-NetFirewallRule -DisplayName "VSS API Server" -Direction Inbound -LocalPort 8001 -Protocol TCP -Action Allow
```

### 데이터베이스 연결 실패

**문제:** MariaDB 연결 오류

**해결:**
1. MariaDB 서버가 실행 중인지 확인
2. `vss-api.py`의 DB 연결 정보 확인 (1492-1496줄)
3. 방화벽에서 3306 포트 허용 확인
4. 사용자 권한 확인

### MoviePy 설치 오류

**문제:** MoviePy 설치 실패

**해결:**
```bash
# FFmpeg 설치 확인
ffmpeg -version

# ImageMagick 없이 설치
pip install moviepy --no-deps
pip install decorator tqdm imageio imageio-ffmpeg
```

### CORS 오류

**문제:** 프론트엔드에서 API 호출 시 CORS 오류

**해결:** `vss-api.py`에서 CORS 미들웨어가 이미 설정되어 있습니다. 백엔드 서버가 올바르게 실행되고 있는지 확인하세요.

### 환경 변수 로드 실패

**문제:** `.env` 파일이 로드되지 않음

**해결:**
1. 프로젝트 루트에 `.env` 파일이 있는지 확인
2. `python-dotenv` 설치 확인: `pip install python-dotenv`
3. 환경 변수 형식 확인 (공백 없이 `KEY=VALUE`)

## 📚 추가 문서

- `SMTP_SETUP_GUIDE.md` - SMTP 이메일 설정 가이드
- `docs/FIX_HOST_DOCKER_INTERNAL.md` - Docker 호스트 설정 가이드

## 🔐 보안 권장사항

1. **프로덕션 환경:**
   - `.env` 파일을 `.gitignore`에 추가
   - `--reload` 옵션 제거
   - HTTPS 사용
   - CORS `allow_origins`를 특정 도메인으로 제한

2. **데이터베이스:**
   - `root` 사용자 대신 전용 사용자 생성
   - 최소 권한 원칙 적용
   - 정기적인 백업

3. **API 키:**
   - 환경 변수로 관리
   - Git에 커밋하지 않기

## 📝 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

## 👥 지원

문제가 발생하면 다음을 확인하세요:
1. 로그 파일 확인
2. 데이터베이스 연결 상태 확인
3. 외부 서비스 (VIA 서버, Ollama) 연결 확인
