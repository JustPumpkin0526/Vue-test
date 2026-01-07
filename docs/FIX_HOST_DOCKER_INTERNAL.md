# host.docker.internal 문제 해결 가이드

## 문제 원인

Windows hosts 파일에 Docker Desktop이 추가한 항목이 남아있어서 MariaDB 클라이언트가 `host.docker.internal`을 호스트명으로 사용합니다.

## 해결 방법

### 방법 1: hosts 파일 수정 (권장)

1. **관리자 권한으로 메모장 실행**
   - 시작 메뉴 → "메모장" 검색
   - 우클릭 → "관리자 권한으로 실행"

2. **hosts 파일 열기**
   - 파일 → 열기
   - 경로 입력: `C:\Windows\System32\drivers\etc\hosts`
   - 파일 형식: "모든 파일" 선택

3. **Docker 관련 항목 주석 처리 또는 삭제**
   
   **수정 전:**
   ```
   # Added by Docker Desktop
   172.16.15.69 host.docker.internal
   172.16.15.69 gateway.docker.internal
   # To allow the same kube context to work on the host and the container:
   127.0.0.1 kubernetes.docker.internal
   # End of section
   ```
   
   **수정 후:**
   ```
   # Added by Docker Desktop (주석 처리됨 - Docker 사용 안 함)
   # 172.16.15.69 host.docker.internal
   # 172.16.15.69 gateway.docker.internal
   # To allow the same kube context to work on the host and the container:
   # 127.0.0.1 kubernetes.docker.internal
   # End of section
   ```

4. **파일 저장**
   - Ctrl + S 또는 파일 → 저장

5. **재부팅** (선택사항, 권장)
   - 변경사항을 완전히 적용하기 위해 재부팅

### 방법 2: MariaDB 서버에서 권한 부여 (임시 해결책)

hosts 파일을 수정하지 않고 DB 서버에서 권한을 부여:

```sql
-- MariaDB 서버에 접속하여 실행
GRANT ALL PRIVILEGES ON vss.* TO 'root'@'host.docker.internal' IDENTIFIED BY 'pass0001!';
FLUSH PRIVILEGES;
```

또는 모든 호스트에서 접근 허용:

```sql
GRANT ALL PRIVILEGES ON vss.* TO 'root'@'%' IDENTIFIED BY 'pass0001!';
FLUSH PRIVILEGES;
```

## 확인 방법

### hosts 파일 확인

CMD에서 확인:
```cmd
type C:\Windows\System32\drivers\etc\hosts | findstr docker
```

항목이 없으면 정상입니다.

### 애플리케이션 테스트

hosts 파일 수정 후 애플리케이션을 재시작하고 로그 확인:
- `host.docker.internal` 에러가 사라져야 합니다
- 또는 MariaDB 서버에서 권한을 부여한 경우 연결이 성공해야 합니다

## 참고

- hosts 파일은 시스템 파일이므로 관리자 권한이 필요합니다
- 파일 수정 후 DNS 캐시를 클리어하려면 재부팅하거나 다음 명령어 실행:
  ```cmd
  ipconfig /flushdns
  ```



