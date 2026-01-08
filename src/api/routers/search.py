"""검색 및 클립 생성 관련 라우터"""
import os
import json
import time
import shutil
import asyncio
import logging
import aiohttp
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Request, File, Form, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from moviepy.video.io.VideoFileClip import VideoFileClip
from database.connection import conn, cursor, ensure_db_connection
from services.video_service import _save_summary_to_db
from utils.helpers import (
    ensure_vss_client, get_via_model, get_recommended_chunk_size,
    create_summarize_prompt, build_query_prompt, build_summarize_params,
    build_query_video_params, get_session
)
from utils.video_utils import parse_timestamps
from config.settings import (
    CLIPS_DIR, TMP_DIR, CLIP_CLEANUP_AGE, DEFAULT_QUERY_TIMESTAMP_SUFFIX,
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, VIA_SERVER_URL
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== 요청 모델 ====================
class RecommendedChunkSizeRequest(BaseModel):
    video_length: float

class RemoveMediaRequest(BaseModel):
    media_ids: List[str]

class DeleteClipsRequest(BaseModel):
    clip_urls: List[str]  # 삭제할 클립 URL 리스트

# ==================== 헬퍼 함수 ====================
async def remove_all_media(session: aiohttp.ClientSession, media_ids):
    """VIA 서버에서 여러 미디어 파일을 삭제하는 함수"""
    for media_id in media_ids:
        try:
            async with session.delete(VIA_SERVER_URL + "/files/" + media_id) as resp:
                if resp.status >= 400:
                    logger.warning(f"Failed to delete media {media_id}: HTTP {resp.status}")
                else:
                    logger.info(f"Successfully deleted media {media_id}")
        except Exception as e:
            logger.error(f"Error deleting media {media_id}: {e}")

# ==================== 엔드포인트 ====================
@router.post("/generate-clips")
async def generate_clips(
    request: Request,
    files: List[UploadFile] = File(None),
    prompt: str = Form(...),
    user_id: Optional[str] = Form(None),
    video_ids: Optional[str] = Form(None)  # JSON 문자열로 전달: {"filename1": video_id1, "filename2": video_id2}
):
    """장면 검색 결과 클립 생성"""
    CLIPS_DIR.mkdir(exist_ok=True)
    
    # 오래된 클립 파일 정리
    try:
        current_time = time.time()
        clips_dir_str = str(CLIPS_DIR.resolve())
        for existing_file in os.listdir(clips_dir_str):
            file_path = os.path.join(clips_dir_str, existing_file)
            try:
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if current_time - file_mtime > CLIP_CLEANUP_AGE:
                        os.remove(file_path)
                        logger.info(f"Deleted old clip: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting old clip {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Error cleaning old clips: {e}")

    grouped_clips = []
    from utils.helpers import vss_client

    # Normalize inputs: support single file param or multiple files
    upload_list = []
    if files:
        upload_list.extend(files)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No file provided")

    # Ensure tmp directory exists
    TMP_DIR.mkdir(exist_ok=True)
    
    try:
        # video_ids 파싱 (JSON 문자열)
        video_id_map = {}
        if video_ids and user_id:
            try:
                video_id_map = json.loads(video_ids) if isinstance(video_ids, str) else video_ids
            except:
                video_id_map = {}
        
        for upfile in upload_list:
            file_path = os.path.basename(upfile.filename)
            tmp_path = str(TMP_DIR / file_path)

            await ensure_vss_client()
            model = await get_via_model()

            TMP_DIR.mkdir(exist_ok=True)
            # 업로드용 임시 파일 실제 저장
            with open(tmp_path, "wb") as buffer:
                shutil.copyfileobj(upfile.file, buffer)

            logger.info(f"Uploaded video saved to {tmp_path}")

            # video_ids에서 내부 DB ID 가져오기 (VIA 서버의 video_id로 변환 필요)
            video_id = None
            db_internal_id = None
            if video_id_map:
                # 파일명으로 내부 DB ID 찾기
                db_internal_id = video_id_map.get(file_path) or video_id_map.get(upfile.filename)
                if db_internal_id:
                    try:
                        ensure_db_connection()
                        # 내부 DB ID로 vss_videos 테이블에서 VIDEO_ID (VIA 서버의 video_id) 조회
                        cursor.execute(
                            "SELECT VIDEO_ID FROM vss_videos WHERE ID = ? AND USER_ID = ?",
                            (db_internal_id, user_id)
                        )
                        video_row = cursor.fetchone()
                        if video_row and video_row[0]:
                            video_id = video_row[0]  # VIA 서버의 video_id
                            logger.info(f"video_ids에서 내부 DB ID {db_internal_id}로 VIDEO_ID {video_id} 조회 성공 (파일명: {file_path})")
                        else:
                            logger.warning(f"내부 DB ID {db_internal_id}에 해당하는 VIDEO_ID를 찾을 수 없습니다.")
                    except Exception as e:
                        logger.warning(f"VIDEO_ID 조회 중 오류: {e}")
            
            # video_id가 없으면 VIA 서버에 업로드하여 video_id 얻기
            if not video_id:
                video_id = await vss_client.upload_video(tmp_path)
                logger.info(f"VIA 서버에 업로드하여 video_id 획득: {video_id}")

            video_clips = []
            # MoviePy에 파일 경로(문자열)로 전달
            video = VideoFileClip(tmp_path)
            duration = video.duration or 0
            logger.info(f"Video duration: {duration} seconds for {tmp_path}")
            
            # chunk_duration 계산
            chunk_duration = await get_recommended_chunk_size(duration)

            # DB에서 요약 결과 확인 (user_id와 video_id가 있는 경우)
            has_stored_summary = False
            if user_id and video_id:
                try:
                    ensure_db_connection()
                    # VIDEO_ID (VIA 서버의 video_id)로 요약 결과 확인
                    cursor.execute(
                        """SELECT ID FROM vss_summaries 
                           WHERE VIDEO_ID = ? AND USER_ID = ?""",
                        (video_id, user_id)
                    )
                    if cursor.fetchone():
                        has_stored_summary = True
                        logger.info(f"저장된 요약 결과 발견: VIDEO_ID {video_id}, summarize_video 건너뛰기")
                except Exception as e:
                    logger.warning(f"요약 결과 확인 중 오류: {e}")

            # 요약 파라미터 준비 (Ollama를 사용하여 프롬프트 생성)
            AI_prompt = await create_summarize_prompt(prompt)
            
            # 저장된 요약이 있으면 PROMPT를 비교하여 프롬프트가 변경되었는지 확인
            if has_stored_summary and user_id and video_id:
                try:
                    ensure_db_connection()
                    cursor.execute(
                        """SELECT PROMPT FROM vss_summaries WHERE VIDEO_ID = ? AND USER_ID = ?;""",
                        (video_id, user_id)
                    )
                    summary_row = cursor.fetchone()
                    if summary_row and summary_row[0]:
                        stored_prompt = summary_row[0]
                        # 저장된 PROMPT와 현재 AI_prompt를 비교
                        if stored_prompt.strip() == AI_prompt.strip():
                            has_stored_summary = True
                            logger.info(f"프롬프트가 동일하여 저장된 요약을 사용합니다. (VIDEO_ID: {video_id})")
                        else:
                            has_stored_summary = False
                            logger.info(f"프롬프트가 변경되어 요약을 다시 수행합니다. (VIDEO_ID: {video_id})")
                    else:
                        has_stored_summary = False
                        logger.info(f"저장된 PROMPT가 없어 요약을 다시 수행합니다. (VIDEO_ID: {video_id})")
                except Exception as e:
                    logger.warning(f"PROMPT 조회 중 오류: {e}")
                    has_stored_summary = False

            if not has_stored_summary:
                logger.info(f"AI_prompt: {AI_prompt}")
                summarize_params = build_summarize_params(
                    video_id=video_id,
                    chunk_duration=chunk_duration,
                    model=model,
                    prompt=AI_prompt,
                    temperature=0,
                    summarize_temperature=0,
                    chat_temperature=0,
                    notification_temperature=0
                )
                result = await vss_client.summarize_video(*summarize_params)
                
                # 요약 결과를 DB에 저장
                if user_id and video_id and result:
                    try:
                        summary_text = result
                        if isinstance(result, dict):
                            summary_text = result.get("content", str(result))
                        elif not isinstance(result, str):
                            summary_text = str(result)
                        
                        _save_summary_to_db(video_id, user_id, summary_text, AI_prompt)
                    except Exception as e:
                        logger.error(f"요약 결과 DB 저장 실패: {e}")
            else:
                logger.info(f"저장된 요약 결과가 있어 summarize_video를 건너뜁니다. 바로 query_video로 진행합니다.")
            
            # prompt를 질문으로 처리: VIA 서버의 query_video 사용
            try:
                enhanced_prompt = await build_query_prompt(prompt + DEFAULT_QUERY_TIMESTAMP_SUFFIX)

                logger.info(f"enhanced_prompt: {enhanced_prompt}")
                
                query_params = build_query_video_params(
                    video_id=video_id,
                    model=model,
                    query=enhanced_prompt,
                    chunk_size=chunk_duration,
                    temperature=0
                )
                
                query_result = await vss_client.query_video(*query_params)
                
                # query_result를 Ollama LLM에 보내서 타임스탬프만 추출
                extracted_timestamps_text = None
                try:
                    timestamp_extraction_prompt = f"""다음은 동영상 질의 응답 결과입니다:
{query_result}

위 응답에서 타임스탬프만 추출하여 반드시 '시작시간-끝시간' 형태로만 출력해주세요. 타임스탬프 형식은 초 단위(예: 10.5-120.3) 또는 분:초 형식(예: 1:30-2:45)일 수 있습니다. 타임스탬프만 출력하고 다른 설명은 포함하지 마세요."""
                    
                    session = await get_session()
                    ollama_url = f"{OLLAMA_BASE_URL}/api/chat"
                    payload = {
                        "model": OLLAMA_MODEL,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert at extracting timestamps from video query responses. Extract only timestamps and output them in a clear format."
                            },
                            {
                                "role": "user",
                                "content": timestamp_extraction_prompt
                            }
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0,
                            "num_predict": 500
                        }
                    }
                    
                    async with session.post(
                        ollama_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT)
                    ) as ollama_response:
                        if ollama_response.status == 200:
                            ollama_data = await ollama_response.json()
                            extracted_timestamps_text = ollama_data.get("message", {}).get("content", "")
                            if extracted_timestamps_text:
                                extracted_timestamps_text = extracted_timestamps_text.strip()
                except aiohttp.ClientConnectorError as e:
                    logger.error(f"Ollama 서버에 연결할 수 없습니다: {e}")
                    logger.warning("Ollama 연결 실패로 타임스탬프 추출을 건너뜁니다.")
                except asyncio.TimeoutError as e:
                    logger.error(f"Ollama 서버 응답 시간 초과: {e}")
                    logger.warning("Ollama 연결 타임아웃으로 타임스탬프 추출을 건너뜁니다.")
                except Exception as e:
                    logger.error(f"Ollama를 사용한 타임스탬프 추출 중 오류 발생: {e}")
                    logger.warning("Ollama 오류로 타임스탬프 추출을 건너뜁니다.")
                
                logger.info(f"VIA 서버 답변: {query_result}")
                
                # 추출된 타임스탬프를 파싱하여 클립 생성에 사용
                timestamp_ranges = []
                if extracted_timestamps_text:
                    timestamp_ranges = parse_timestamps(extracted_timestamps_text, duration)
                
                # 타임스탬프 기반 클립 생성
                base_name, _ = os.path.splitext(file_path)
                timestamp_suffix = int(time.time() * 1000)
                
                if timestamp_ranges:
                    clip_index = 0
                    for start_time, end_time in timestamp_ranges:
                        if end_time - start_time <= 0:
                            logger.warning(f"타임스탬프 간격이 0초 이하인 클립을 건너뜁니다: {start_time} - {end_time}")
                            continue
                        
                        clip_filename = f"clip_{base_name}_{timestamp_suffix}_{clip_index+1}.mp4"
                        clip_path = str(CLIPS_DIR / clip_filename)
                        try:
                            video.subclip(start_time, end_time).write_videofile(
                                clip_path,
                                codec="libx264",
                                audio=False,
                                verbose=False
                            )
                            base = str(request.base_url).rstrip('/')
                            clip_url = f"{base}/clips/{clip_filename}"
                            video_clips.append({
                                "id": f"{base_name}_{timestamp_suffix}_{clip_index}",
                                "title": clip_filename,
                                "url": clip_url,
                                "start_time": start_time,
                                "end_time": end_time,
                                "search_query": prompt
                            })
                            clip_index += 1
                        except Exception as e:
                            logger.error(f"Error generating clip {clip_filename}: {e}")
                        time.sleep(0.5)
                else:
                    logger.warning(f"타임스탬프를 찾을 수 없습니다. 검색어: '{prompt}'. VIA 서버 답변을 반환합니다.")
                    video_clips.append({
                        "id": f"{base_name}_{timestamp_suffix}_no_timestamp",
                        "title": "VIA 서버 응답",
                        "url": None,
                        "start_time": None,
                        "end_time": None,
                        "search_query": prompt,
                        "via_response": query_result
                    })
            except HTTPException:
                raise
            except Exception as via_error:
                logger.error(f"VIA 서버 query_video 실패: {via_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"검색 실패: VIA 서버에서 장면 검색 중 오류가 발생했습니다. ({str(via_error)})"
                )
            finally:
                video.close()
                del video

            grouped_clips.append({
                "video": file_path,
                "clips": video_clips
            })

    except Exception as e:
        logger.error(f"Error processing uploaded video(s): {e}")
        raise HTTPException(status_code=500, detail=f"Error processing uploaded video(s): {e}")

    # 클립 추출 여부 확인
    clips_extracted = False
    for group in grouped_clips:
        for clip in group.get("clips", []):
            if clip.get("url") and not clip.get("via_response"):
                clips_extracted = True
                break
        if clips_extracted:
            break
    
    logger.info("All clips generated successfully.")
    return JSONResponse(content={"clips": grouped_clips, "clips_extracted": clips_extracted})

@router.post("/vss-query")
async def vss_query(
    video_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = None,
    chunk_size: int = Form(...),
    temperature: float = Form(...),
    seed: int = Form(...),
    max_new_tokens: int = Form(...),
    top_p: float = Form(...),
    top_k: int = Form(...),
    query: str = Form(...)
):
    """동영상 검색 VSS API"""
    await ensure_vss_client()
    model = await get_via_model()
    from utils.helpers import vss_client

    if file and not video_id:
        TMP_DIR.mkdir(exist_ok=True)
        file_path = str(TMP_DIR / file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        video_id = await vss_client.upload_video(file_path)
    elif not video_id:
        raise HTTPException(status_code=400, detail="video_id 또는 file 중 하나는 필요합니다.")
    
    query_params = build_query_video_params(
        video_id=video_id,
        model=model,
        query=query,
        chunk_size=chunk_size,
        temperature=temperature,
        seed=seed,
        max_new_tokens=max_new_tokens,
        top_p=top_p,
        top_k=top_k
    )
    result = await vss_client.query_video(*query_params)

    return {"summary": result, "video_id": video_id}

@router.get("/via-files")
async def list_via_files(
    purpose: str = Query(default="vision", description="파일 목적 (기본값: vision)")
):
    """VIA 서버에 업로드된 파일 목록 조회"""
    try:
        await ensure_vss_client()
        from utils.helpers import vss_client
        result = await vss_client.list_files(purpose=purpose)
        logger.info(f"VIA 파일 목록 조회 완료: purpose={purpose}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VIA 파일 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"VIA 파일 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/get-recommended-chunk-size")
async def get_recommended_chunk_size_endpoint(request: RecommendedChunkSizeRequest):
    """동영상 길이를 받아서 추천 chunk_size를 반환하는 엔드포인트"""
    try:
        recommended_chunk_size = await get_recommended_chunk_size(request.video_length)
        return {"recommended_chunk_size": recommended_chunk_size, "video_length": request.video_length}
    except Exception as e:
        logger.error(f"Error getting recommended chunk size: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recommended chunk size: {e}")

@router.post("/remove-media")
async def remove_media_endpoint(request: RemoveMediaRequest):
    """VIA 서버에서 미디어 파일들을 삭제하는 엔드포인트"""
    try:
        session = await get_session()
        await remove_all_media(session, request.media_ids)
        return {"success": True, "message": f"Deleted {len(request.media_ids)} media file(s)"}
    except Exception as e:
        logger.error(f"Error removing media: {e}")
        raise HTTPException(status_code=500, detail=f"Error removing media: {e}")

@router.post("/delete-clips")
async def delete_clips(request: DeleteClipsRequest):
    """클립 파일들을 삭제하는 엔드포인트"""
    try:
        if not CLIPS_DIR.exists():
            return {"success": True, "message": "클립 디렉토리가 없습니다.", "deleted_count": 0}
        
        deleted_count = 0
        failed_count = 0
        
        for clip_url in request.clip_urls:
            try:
                # URL에서 파일명 추출
                if "/clips/" in clip_url:
                    filename = clip_url.split("/clips/")[-1].split("?")[0]
                else:
                    filename = clip_url.replace("/clips/", "").split("?")[0]
                
                if not filename:
                    logger.warning(f"클립 파일명을 추출할 수 없습니다: {clip_url}")
                    failed_count += 1
                    continue
                
                clip_file_path = CLIPS_DIR / filename
                
                if clip_file_path.exists() and clip_file_path.is_file():
                    clip_file_path.unlink()
                    deleted_count += 1
                    logger.info(f"클립 파일 삭제 성공: {filename}")
                else:
                    logger.warning(f"클립 파일을 찾을 수 없습니다: {filename}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"클립 삭제 중 오류 발생 ({clip_url}): {e}")
                failed_count += 1
        
        return {
            "success": True,
            "message": f"{deleted_count}개의 클립이 삭제되었습니다.",
            "deleted_count": deleted_count,
            "failed_count": failed_count
        }
    except Exception as e:
        logger.error(f"클립 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"클립 삭제 중 오류가 발생했습니다: {str(e)}")

