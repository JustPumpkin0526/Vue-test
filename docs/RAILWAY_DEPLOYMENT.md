# Railway 배포 가이드

이 가이드는 VSS 백엔드 API 서버를 Railway에 배포하는 방법을 설명합니다.

## 📋 사전 준비

1. **Railway 계정 생성**
   - [Railway](https://railway.app)에 가입
   - GitHub 계정으로 연동 권장

2. **GitHub 저장소 준비**
   - 프로젝트를 GitHub에 푸시
   - Railway가 접근할 수 있도록 설정

## 🚀 배포 단계

### 1단계: Railway 프로젝트 생성

1. Railway 대시보드에서 **"New Project"** 클릭
2. **"Deploy from GitHub repo"** 선택
3. 저장소 선택 및 연결

### 2단계: 환경 변수 설정

Railway 대시보드의 **Variables** 탭에서 다음 환경 변수를 설정합니다:

#### 필수 환경 변수

```env
# 데이터베이스 연결 정보
DB_HOST=172.16.15.69
DB_PORT=3306
DB_USER=root
DB_PASSWORD=pass0001!
DB_NAME=vss

# VIA 서버 주소
VIA_SERVER_URL=http://172.16.7.64:8101

# Ollama 설정 (선택사항)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# 포트 (Railway가 자동 설정, 수정 불필요)
PORT=8001
```

#### 보안 권장사항

- **DB_PASSWORD**: 강력한 비밀번호 사용
- **VIA_SERVER_URL**: 외부에서 접근 가능한 주소로 설정
- 프로덕션 환경에서는 민감한 정보를 Railway의 Secrets로 관리

### 3단계: Railway 설정 (중요!)

Railway 대시보드에서 다음 설정을 해야 합니다:

1. **Settings** → **Source** 탭으로 이동
2. **Root Directory**를 `src/api`로 설정
   - 이렇게 하면 Railway가 `src/api` 디렉토리만 배포합니다
   - Node.js 빌드 오류를 방지할 수 있습니다

또는 Railway가 자동으로 인식하는 파일들:

- **`src/api/requirements.txt`**: Python 의존성
- **`src/api/Procfile`**: 실행 명령어
- **`src/api/nixpacks.toml`**: 빌드 설정 (우선순위 높음)
- **`src/api/railway.json`**: 배포 설정 (선택사항)

### 4단계: 배포 실행

1. Railway가 자동으로 배포를 시작합니다
2. **Deployments** 탭에서 배포 상태 확인
3. 배포 완료 후 **Settings** → **Networking**에서 공개 URL 확인

### 5단계: 프론트엔드 설정

배포 완료 후 Railway에서 제공하는 API URL을 프론트엔드에 설정합니다.

#### GitHub Pages 배포 시

**방법 1: GitHub Actions 사용 (권장)**

`.github/workflows/deploy.yml` 파일 생성:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm install
      
      - name: Build
        run: npm run build
        env:
          VITE_API_BASE_URL: ${{ secrets.RAILWAY_API_URL }}
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
```

**방법 2: 로컬 빌드 후 배포**

`.env.production` 파일 생성:

```env
VITE_API_BASE_URL=https://your-railway-app.railway.app
```

빌드 및 배포:

```bash
npm run build
# dist 폴더를 GitHub Pages에 배포
```

## 🔧 문제 해결

### 배포 실패

1. **로그 확인**: Railway 대시보드의 **Deployments** → **View Logs**
2. **의존성 오류**: `requirements.txt` 확인
3. **포트 오류**: Railway는 `$PORT` 환경 변수를 자동 설정

### DB 연결 실패

1. **방화벽 설정**: DB 서버가 Railway의 IP에서 접근 가능한지 확인
2. **연결 정보**: 환경 변수 값 확인
3. **네트워크**: Railway와 DB 서버 간 네트워크 연결 확인

### CORS 오류

현재 CORS는 `allow_origins=["*"]`로 설정되어 있어 모든 도메인에서 접근 가능합니다.
프로덕션 환경에서는 특정 도메인만 허용하도록 수정하는 것을 권장합니다.

## 📝 추가 설정

### 정적 파일 경로

Railway는 임시 파일 시스템을 사용하므로, 업로드된 파일과 클립은 영구 저장소가 필요합니다.

**권장 솔루션**:
- AWS S3, Google Cloud Storage 등 객체 저장소 사용
- 또는 Railway의 Volume 기능 사용 (유료 플랜)

### 로그 확인

Railway 대시보드의 **Logs** 탭에서 실시간 로그를 확인할 수 있습니다.

## 🔐 보안 체크리스트

- [ ] DB 비밀번호를 강력하게 설정
- [ ] 환경 변수를 Railway Secrets로 관리
- [ ] CORS 설정을 프로덕션 도메인으로 제한
- [ ] HTTPS 사용 (Railway 자동 제공)
- [ ] 민감한 정보를 코드에 하드코딩하지 않음

## 📞 지원

문제가 발생하면 Railway 로그를 확인하거나 Railway 지원팀에 문의하세요.

