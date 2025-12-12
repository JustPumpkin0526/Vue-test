# Railway SMTP 설정 가이드

Railway에 배포된 API 서버에서 이메일 인증 코드를 발송하기 위한 SMTP 설정 방법입니다.

## 문제 상황

외부 환경에서 회원가입 시 인증 코드가 발송되지 않는 경우, Railway 환경 변수에 SMTP 설정이 없기 때문입니다.

## 해결 방법

### 1. Railway 환경 변수 설정

Railway 대시보드에서:

1. 프로젝트 → **Variables** 탭 클릭
2. 다음 환경 변수들을 추가:

#### Gmail 사용 시 (권장)

| 이름 | 값 | 설명 |
|-----|-----|------|
| `SMTP_SERVER` | `smtp.gmail.com` | Gmail SMTP 서버 |
| `SMTP_PORT` | `587` | TLS 포트 (또는 465) |
| `SMTP_USER` | `your-email@gmail.com` | Gmail 주소 |
| `SMTP_PASSWORD` | `your-app-password` | Gmail 앱 비밀번호 (16자리) |
| `SMTP_FROM_EMAIL` | `your-email@gmail.com` | 발신자 이메일 (보통 USER와 동일) |

#### Outlook/Hotmail 사용 시

| 이름 | 값 |
|-----|-----|
| `SMTP_SERVER` | `smtp-mail.outlook.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `your-email@outlook.com` |
| `SMTP_PASSWORD` | `your-password` |
| `SMTP_FROM_EMAIL` | `your-email@outlook.com` |

#### Naver 사용 시

| 이름 | 값 |
|-----|-----|
| `SMTP_SERVER` | `smtp.naver.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | `your-email@naver.com` |
| `SMTP_PASSWORD` | `your-password` |
| `SMTP_FROM_EMAIL` | `your-email@naver.com` |

### 2. Gmail 앱 비밀번호 생성 (Gmail 사용 시 필수)

Gmail을 사용하는 경우 일반 비밀번호가 아닌 **앱 비밀번호**를 사용해야 합니다:

1. [Google 계정 설정](https://myaccount.google.com/) 접속
2. **보안** 탭 클릭
3. **2단계 인증** 활성화 (필수)
4. **앱 비밀번호** 클릭
5. 앱 선택: **메일**
6. 기기 선택: **기타(맞춤 이름)** → "VSS" 또는 "Railway" 입력
7. **생성** 클릭
8. 생성된 16자리 비밀번호 복사 (예: `abcd efgh ijkl mnop`)
9. Railway 환경 변수 `SMTP_PASSWORD`에 입력 (공백 포함 가능)

**⚠️ 중요:**
- 일반 Gmail 비밀번호는 작동하지 않습니다
- 반드시 앱 비밀번호를 사용해야 합니다
- 2단계 인증이 활성화되어 있어야 합니다

### 3. Railway 서비스 재시작

환경 변수 추가 후:

1. Railway 대시보드 → **Deployments** 탭
2. 최신 배포 클릭
3. **Redeploy** 클릭 (또는 자동 재배포 대기)

### 4. SMTP 설정 확인

Railway 로그에서 확인:

1. Railway 대시보드 → **Deployments** → **View Logs**
2. 다음 메시지 확인:

**정상 설정 시:**
```
SMTP 설정 로드 완료: SERVER=smtp.gmail.com, PORT=587, USER=you***
```

**설정 누락 시:**
```
⚠️ SMTP 설정이 로드되지 않았습니다!
   SMTP_USER: 비어있음
   SMTP_PASSWORD: 비어있음
```

### 5. 테스트

1. Vercel 배포된 사이트 접속
2. 회원가입 페이지에서 이메일 입력
3. "인증 코드 전송" 버튼 클릭
4. 이메일 수신 확인

## 문제 해결

### 인증 코드가 발송되지 않는 경우

1. **Railway 로그 확인**
   - Railway 대시보드 → Deployments → View Logs
   - SMTP 관련 에러 메시지 확인

2. **환경 변수 확인**
   - Railway → Variables 탭
   - 모든 SMTP 환경 변수가 설정되어 있는지 확인
   - 값에 공백이나 특수문자가 없는지 확인

3. **Gmail 앱 비밀번호 확인**
   - 일반 비밀번호가 아닌 앱 비밀번호 사용
   - 16자리 비밀번호 확인
   - 2단계 인증 활성화 확인

4. **포트 확인**
   - Gmail: 587 (TLS) 또는 465 (SSL)
   - Railway에서 포트가 차단되지 않았는지 확인

### 일반적인 에러 메시지

#### `SMTPAuthenticationError`
```
SMTP 인증 실패: (535, '5.7.8 Username and Password not accepted')
```

**해결:**
- Gmail의 경우 앱 비밀번호 사용 확인
- 사용자명과 비밀번호 정확성 확인
- 계정이 잠겨있지 않은지 확인

#### `SMTPConnectError`
```
SMTP 연결 실패: [Errno 111] Connection refused
```

**해결:**
- SMTP_SERVER 주소 확인
- 포트 번호 확인 (587 또는 465)
- 방화벽 설정 확인

#### `SMTP 설정이 로드되지 않았습니다`
```
⚠️ SMTP 설정이 로드되지 않았습니다!
```

**해결:**
- Railway 환경 변수에 SMTP 설정 추가
- 환경 변수 이름 정확성 확인 (`SMTP_USER`, `SMTP_PASSWORD` 등)
- Railway 서비스 재시작

## 보안 주의사항

⚠️ **중요:**
- SMTP 비밀번호는 절대 코드에 하드코딩하지 마세요
- Railway 환경 변수는 안전하게 관리됩니다
- Gmail 앱 비밀번호는 정기적으로 갱신하는 것을 권장합니다
- 프로덕션 환경에서는 전용 이메일 계정 사용 권장

## 추가 리소스

- [Gmail 앱 비밀번호 생성](https://myaccount.google.com/apppasswords)
- [Railway 환경 변수 문서](https://docs.railway.app/develop/variables)
- [SMTP 설정 가이드](./SMTP_SETUP_GUIDE.md)

