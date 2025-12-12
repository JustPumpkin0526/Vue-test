# Railway API 배포를 위한 GitHub 파일 목록

Railway에 API를 배포하기 위해 GitHub에 올려야 하는 필수 파일들을 정리했습니다.

## ✅ 필수 파일 (반드시 필요)

### 1. API 서버 파일
- **`src/api/vss-api.py`** - 메인 FastAPI 애플리케이션 파일

### 2. Python 의존성
- **`src/api/requirements.txt`** - Python 패키지 의존성 목록

### 3. 배포 설정 파일 (하나 이상 필요)

#### 옵션 A: Procfile 사용
- **`src/api/Procfile`** - Railway 실행 명령어 정의

#### 옵션 B: nixpacks.toml 사용 (권장)
- **`src/api/nixpacks.toml`** - Nixpacks 빌드 설정

#### 옵션 C: railway.json 사용
- **`src/api/railway.json`** - Railway 배포 설정

## 📁 현재 프로젝트 구조

```
프로젝트 루트/
├── src/
│   └── api/
│       ├── vss-api.py          ✅ 필수
│       ├── requirements.txt    ✅ 필수
│       ├── Procfile            ✅ 필수 (옵션 A)
│       ├── nixpacks.toml       ✅ 필수 (옵션 B, 권장)
│       └── railway.json        ⚠️ 선택사항
│
├── src/
│   └── assets/
│       └── sample/
│           └── sample.mp4       ⚠️ 선택사항 (샘플 비디오)
│
└── .github/
    └── workflows/
        └── deploy.yml          ⚠️ 선택사항 (프론트엔드 배포용)
```

## 🔧 Railway 대시보드 설정

GitHub에 파일을 올린 후, Railway 대시보드에서 다음을 설정해야 합니다:

### 1. Root Directory 설정
- **Settings** → **Source** → **Root Directory**: `src/api`로 설정
- 이렇게 하면 Railway가 `src/api` 디렉토리만 배포합니다

### 2. 환경 변수 설정
- **Variables** 탭에서 다음 환경 변수 추가:

```env
DB_HOST=172.16.15.69
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=vss
VIA_SERVER_URL=http://172.16.7.64:8101
```

## 📝 파일별 상세 설명

### `src/api/vss-api.py`
- FastAPI 애플리케이션의 메인 파일
- 모든 API 엔드포인트가 정의되어 있음
- **반드시 필요**

### `src/api/requirements.txt`
- Python 패키지 의존성 목록
- Railway가 자동으로 `pip install -r requirements.txt` 실행
- **반드시 필요**

### `src/api/Procfile`
- Railway가 애플리케이션을 실행하는 명령어 정의
- 형식: `web: <실행 명령어>`
- **Procfile 또는 nixpacks.toml 중 하나 필요**

### `src/api/nixpacks.toml`
- Nixpacks 빌드 시스템 설정 파일
- 빌드 단계와 실행 명령어 정의
- **Procfile보다 우선순위가 높음 (권장)**

### `src/api/railway.json`
- Railway 전용 배포 설정 파일
- 빌드 명령어와 시작 명령어 정의
- **선택사항** (nixpacks.toml 또는 Procfile이 있으면 충분)

## ⚠️ 주의사항

### 올리면 안 되는 파일
- `.env` 파일 (환경 변수는 Railway 대시보드에서 설정)
- `__pycache__/` 폴더
- `clips/`, `videos/`, `tmp/` 폴더 (런타임 생성 폴더)
- `node_modules/` (프론트엔드 의존성)

### .gitignore 확인
다음 항목들이 `.gitignore`에 포함되어 있는지 확인:
```
__pycache__/
*.pyc
.env
.env.local
clips/
videos/
tmp/
node_modules/
dist/
```

## 🚀 배포 체크리스트

배포 전에 다음을 확인하세요:

- [ ] `src/api/vss-api.py` 파일이 GitHub에 올라가 있음
- [ ] `src/api/requirements.txt` 파일이 GitHub에 올라가 있음
- [ ] `src/api/Procfile` 또는 `src/api/nixpacks.toml` 파일이 GitHub에 올라가 있음
- [ ] Railway 대시보드에서 Root Directory를 `src/api`로 설정
- [ ] Railway 대시보드에서 환경 변수 설정 완료
- [ ] GitHub 저장소가 Railway에 연결되어 있음

## 📚 관련 문서

- 상세한 배포 가이드: [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
- 문제 해결: [RAILWAY_DEPLOYMENT.md#문제-해결](./RAILWAY_DEPLOYMENT.md#문제-해결)

