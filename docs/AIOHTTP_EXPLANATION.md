# aiohttp란 무엇인가?

## aiohttp 개요

**aiohttp**는 Python의 **비동기(asynchronous) HTTP 클라이언트/서버 라이브러리**입니다.

### 주요 특징

1. **비동기 처리**: `async/await` 문법을 사용하여 비동기 HTTP 요청/응답 처리
2. **높은 성능**: 동시에 여러 HTTP 요청을 처리할 수 있어 성능이 우수
3. **웹소켓 지원**: HTTP뿐만 아니라 WebSocket 통신도 지원
4. **세션 관리**: 연결 풀링과 세션 재사용으로 효율적인 리소스 관리

## vss-api.py에서 aiohttp를 사용하는 이유

### 1. FastAPI와의 호환성

FastAPI는 **비동기 프레임워크**입니다. 외부 서버(VIA 서버, Ollama 서버)에 HTTP 요청을 보낼 때:

- ❌ **동기 라이브러리 사용 시** (예: `requests`):
  ```python
  # 동기 방식 - 블로킹 발생
  response = requests.get("http://via-server/models")  # 이 동안 다른 요청 처리 불가
  ```

- ✅ **비동기 라이브러리 사용 시** (예: `aiohttp`):
  ```python
  # 비동기 방식 - 블로킹 없음
  async with session.get("http://via-server/models") as resp:  # 다른 요청 동시 처리 가능
      data = await resp.json()
  ```

### 2. 동시 요청 처리 성능 향상

`vss-api.py`에서는 여러 외부 서버와 통신합니다:

- **VIA 서버**: 동영상 처리, 요약, 질의 응답
- **Ollama 서버**: 타임스탬프 추출

비동기 처리를 통해:
- 여러 요청을 동시에 처리 가능
- 서버 응답을 기다리는 동안 다른 작업 수행 가능
- 전체 처리 시간 단축

### 3. 메모리 효율성

대용량 파일 업로드 시 스트리밍 방식으로 처리:

```python
# aiohttp를 사용한 스트리밍 업로드
data = aiohttp.FormData()
file_handle = open(video_path, "rb")
data.add_field("file", file_handle, filename="video.mp4")
# 메모리에 전체 파일을 로드하지 않고 스트리밍으로 전송
```

### 4. 세션 재사용

전역 세션을 재사용하여 연결 오버헤드 감소:

```python
# 전역 세션 관리
http_session: Optional[aiohttp.ClientSession] = None

async def get_session():
    """전역 aiohttp 세션 가져오기 또는 생성"""
    global http_session
    if http_session is None or http_session.closed:
        http_session = aiohttp.ClientSession()
    return http_session
```

## vss-api.py에서의 사용 예시

### 1. VIA 서버 모델 조회

```python
async def get_model(self):
    session = await get_session()
    async with session.get(self.models_endpoint, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        json_data = await self.check_response(resp)
        return json_data["data"][0]["id"]
```

### 2. 동영상 업로드 (스트리밍)

```python
async def upload_video(self, video_path):
    session = await get_session()
    data = aiohttp.FormData()
    file_handle = open(video_path, "rb")
    data.add_field("file", file_handle, filename="video.mp4")
    
    async with session.post(
        self.files_endpoint, 
        data=data,
        timeout=aiohttp.ClientTimeout(total=timeout_seconds)
    ) as response:
        json_data = await self.check_response(response)
        return json_data.get("id")
```

### 3. Ollama API 호출

```python
async with session.post(
    ollama_url,
    json=payload,
    timeout=aiohttp.ClientTimeout(total=60)
) as ollama_response:
    if ollama_response.status == 200:
        ollama_data = await ollama_response.json()
        extracted_timestamps_text = ollama_data.get("message", {}).get("content", "")
```

## 동기 vs 비동기 비교

### 동기 방식 (requests 사용 시)

```python
# 문제점: 각 요청이 순차적으로 실행됨
def process_video():
    # 1. VIA 서버에 모델 조회 (2초 대기)
    models = requests.get("http://via-server/models")
    
    # 2. 동영상 업로드 (10초 대기)
    video_id = requests.post("http://via-server/files", files=file)
    
    # 3. 요약 요청 (30초 대기)
    summary = requests.post("http://via-server/summarize", json=data)
    
    # 총 시간: 2 + 10 + 30 = 42초
```

### 비동기 방식 (aiohttp 사용 시)

```python
# 장점: 여러 요청을 동시에 처리하거나, 대기 시간 동안 다른 작업 수행
async def process_video():
    session = await get_session()
    
    # 1. 모델 조회 (2초 대기, 하지만 다른 작업 가능)
    async with session.get("http://via-server/models") as resp:
        models = await resp.json()
    
    # 2. 동영상 업로드 (10초 대기, 하지만 다른 요청 처리 가능)
    async with session.post("http://via-server/files", data=form_data) as resp:
        video_id = await resp.json()
    
    # 3. 요약 요청 (30초 대기, 하지만 다른 요청 처리 가능)
    async with session.post("http://via-server/summarize", json=data) as resp:
        summary = await resp.json()
    
    # 실제 대기 시간은 동일하지만, 다른 사용자 요청을 동시에 처리 가능
```

## 주요 장점 요약

1. **성능**: 동시에 여러 요청 처리로 전체 처리량 증가
2. **확장성**: 많은 동시 사용자 요청 처리 가능
3. **효율성**: 서버 응답 대기 중에도 다른 작업 수행
4. **메모리**: 스트리밍 방식으로 대용량 파일 처리 시 메모리 효율적
5. **FastAPI 호환**: FastAPI의 비동기 특성과 완벽하게 호환

## 대안 라이브러리

만약 동기 라이브러리를 사용한다면:

- `requests`: 가장 인기 있는 동기 HTTP 라이브러리
- `httpx`: 비동기와 동기 모두 지원 (aiohttp의 대안)

하지만 FastAPI와 함께 사용할 때는 **aiohttp**가 가장 적합합니다.

## 참고 자료

- [aiohttp 공식 문서](https://docs.aiohttp.org/)
- [FastAPI 비동기 가이드](https://fastapi.tiangolo.com/async/)
- [Python asyncio 문서](https://docs.python.org/3/library/asyncio.html)

