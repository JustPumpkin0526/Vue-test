# Vue 애플리케이션 배포 가이드

이 가이드는 VSS Vue 애플리케이션을 프로덕션 환경에 배포하는 방법을 설명합니다.

## 📋 목차

1. [프로덕션 빌드](#1-프로덕션-빌드)
2. [환경 변수 설정](#2-환경-변수-설정)
3. [배포 옵션](#3-배포-옵션)
4. [백엔드 연동](#4-백엔드-연동)
5. [문제 해결](#5-문제-해결)

---

## 1. 프로덕션 빌드

### 1.1 빌드 명령어

```bash
# 의존성 설치 (처음 한 번만)
npm install

# 프로덕션 빌드
npm run build
```

### 1.2 빌드 결과물

빌드가 완료되면 `dist/` 폴더에 다음 파일들이 생성됩니다:

```
dist/
├── index.html          # 진입점 HTML
├── assets/
│   ├── index-*.js      # 번들된 JavaScript
│   ├── index-*.css     # 번들된 CSS
│   └── *.png           # 이미지 리소스
└── favicon.ico
```

### 1.3 빌드 확인

```bash
# 로컬에서 빌드 결과물 미리보기
npm run preview
```

브라우저에서 `http://localhost:4173`으로 접속하여 확인할 수 있습니다.

---

## 2. 환경 변수 설정

현재 프로젝트는 API 엔드포인트가 하드코딩되어 있습니다. 배포 전에 환경 변수를 사용하도록 수정하는 것을 권장합니다.

### 2.1 Vite 환경 변수 설정

Vite는 `.env` 파일을 지원합니다:

**`.env.development`** (개발 환경)
```env
VITE_API_BASE_URL=http://localhost:8001
```

**`.env.production`** (프로덕션 환경)
```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

### 2.2 코드에서 환경 변수 사용

```javascript
// src/config/api.js (새로 생성)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export default {
  baseURL: API_BASE_URL,
  endpoints: {
    upload: `${API_BASE_URL}/upload-video`,
    videos: `${API_BASE_URL}/videos`,
    summarize: `${API_BASE_URL}/vss-summarize`,
    query: `${API_BASE_URL}/vss-query`,
    // ... 기타 엔드포인트
  }
};
```

### 2.3 기존 코드 수정

모든 `http://localhost:8001`을 환경 변수로 교체:

```javascript
// Before
const response = await fetch('http://localhost:8001/videos?user_id=...');

// After
import apiConfig from '@/config/api';
const response = await fetch(`${apiConfig.endpoints.videos}?user_id=...`);
```

---

## 3. 배포 옵션

### 3.1 정적 호스팅 서비스

#### **Vercel** (추천)

1. [Vercel](https://vercel.com)에 가입
2. GitHub 저장소 연결
3. 빌드 설정:
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. 환경 변수 추가:
   - `VITE_API_BASE_URL`: 프로덕션 API URL
5. 배포 완료!

#### **Netlify**

1. [Netlify](https://netlify.com)에 가입
2. "Add new site" → "Deploy manually"
3. `dist` 폴더를 드래그 앤 드롭
4. 환경 변수 설정 (Site settings → Environment variables)

#### **GitHub Pages**

```bash
# vite.config.js에 base 경로 추가
export default defineConfig({
  base: '/your-repo-name/',  # GitHub 저장소 이름
  // ... 기타 설정
})

# 배포 스크립트 추가 (package.json)
"scripts": {
  "deploy": "npm run build && gh-pages -d dist"
}

# gh-pages 설치
npm install --save-dev gh-pages

# 배포
npm run deploy
```

### 3.2 자체 서버 배포

#### **Nginx 설정**

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/vue-test/dist;
    index index.html;

    # SPA 라우팅 지원
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 정적 파일 캐싱
    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 프록시 (선택사항)
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### **Apache 설정**

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    DocumentRoot /var/www/vue-test/dist

    <Directory /var/www/vue-test/dist>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
        
        # SPA 라우팅 지원
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>
</VirtualHost>
```

#### **Docker 배포**

**Dockerfile**
```dockerfile
# 빌드 단계
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 프로덕션 단계
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf**
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**빌드 및 실행**
```bash
docker build -t vue-test .
docker run -d -p 80:80 vue-test
```

---

## 4. 백엔드 연동

### 4.1 CORS 설정 확인

백엔드(`vss-api.py`)에서 CORS가 올바르게 설정되어 있는지 확인:

```python
# vss-api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 개발 환경
        "https://yourdomain.com",  # 프로덕션 환경
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.2 API 엔드포인트 통일

프로덕션에서는 절대 경로 대신 상대 경로 또는 환경 변수를 사용:

```javascript
// ❌ 하드코딩
const API_URL = 'http://localhost:8001';

// ✅ 환경 변수 사용
const API_URL = import.meta.env.VITE_API_BASE_URL;

// ✅ 상대 경로 (같은 도메인)
const API_URL = '/api';  // Nginx 프록시 사용 시
```

### 4.3 백엔드 배포

백엔드는 별도로 배포해야 합니다:

```bash
# 백엔드 실행 (프로덕션)
cd src/api
uvicorn vss-api:app --host 0.0.0.0 --port 8001
```

또는 systemd 서비스로 등록:

```ini
# /etc/systemd/system/vss-api.service
[Unit]
Description=VSS API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Vue-test/src/api
ExecStart=/usr/bin/uvicorn vss-api:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 5. 문제 해결

### 5.1 빌드 오류

```bash
# node_modules 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 5.2 라우팅 문제 (404)

SPA는 모든 경로를 `index.html`로 리다이렉트해야 합니다. Nginx/Apache 설정을 확인하세요.

### 5.3 API 연결 실패

1. 브라우저 개발자 도구 → Network 탭에서 요청 확인
2. CORS 오류 확인
3. 백엔드 서버가 실행 중인지 확인
4. 방화벽 설정 확인

### 5.4 환경 변수 미적용

- 환경 변수는 `VITE_` 접두사가 필요합니다
- 빌드 시점에 환경 변수가 적용됩니다 (런타임이 아님)
- 환경 변수 변경 후 재빌드 필요

---

## 6. 배포 체크리스트

- [ ] 프로덕션 빌드 성공 (`npm run build`)
- [ ] 환경 변수 설정 완료
- [ ] API 엔드포인트 수정 완료
- [ ] CORS 설정 확인
- [ ] SPA 라우팅 설정 확인
- [ ] 정적 파일 캐싱 설정
- [ ] HTTPS 설정 (프로덕션)
- [ ] 백엔드 서버 실행 확인
- [ ] 데이터베이스 연결 확인
- [ ] 로그 모니터링 설정

---

## 추가 리소스

- [Vite 공식 문서](https://vitejs.dev/guide/static-deploy.html)
- [Vue Router 배포 가이드](https://router.vuejs.org/guide/essentials/history-mode.html)
- [Vercel 배포 가이드](https://vercel.com/docs)

