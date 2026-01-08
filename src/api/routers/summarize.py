"""요약 관련 라우터"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Form, UploadFile, HTTPException, Query
from pydantic import BaseModel
from database.connection import conn, cursor, ensure_db_connection, verify_user_exists, validate_video_ownership
from services.video_service import _save_summary_to_db
from utils.helpers import (
    ensure_vss_client, get_via_model, build_summarize_params
)
from config.settings import (
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
)
import aiohttp

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== 요청 모델 ====================
class SaveSummaryRequest(BaseModel):
    video_id: str  # VIA 서버의 video_id (vss_videos.VIDEO_ID 컬럼 값)
    user_id: str
    prompt: str
    summary_text: str
    via_video_id: Optional[str] = None  # VIA 서버의 video_id (하위 호환성을 위해 유지)

class DeleteSummaryRequest(BaseModel):
    video_ids: List[int]  # vss_videos 테이블의 ID 목록 (내부 DB ID)
    user_id: str

# ==================== 엔드포인트 ====================
@router.post("/vss-summarize")
async def vss_summarize(
    file: UploadFile,
    prompt: str = Form(...),
    csprompt: str = Form(...),
    saprompt: str = Form(...),
    chunk_duration: int = Form(...),
    num_frames_per_chunk: int = Form(...),
    frame_width: int = Form(...),
    frame_height: int = Form(...),
    top_k: int = Form(...),
    top_p: float = Form(...),
    temperature: float = Form(...),
    max_tokens: int = Form(...),
    seed: int = Form(...),
    batch_size: int = Form(...),
    rag_batch_size: int = Form(...),
    rag_top_k: int = Form(...),
    summary_top_p: float = Form(...),
    summary_temperature: float = Form(...),
    summary_max_tokens: int = Form(...),
    chat_top_p: float = Form(...),
    chat_temperature: float = Form(...),
    chat_max_tokens: int = Form(...),
    alert_top_p: float = Form(...),
    alert_temperature: float = Form(...),
    alert_max_tokens: int = Form(...),
    enable_audio: bool = Form(...),
    video_id: Optional[str] = Form(None),  # VIA 서버의 video_id (이미 업로드된 경우)
):
    """동영상 요약 VSS API"""
    await ensure_vss_client()
    model = await get_via_model()

    # video_id가 제공되지 않은 경우에만 업로드 (하지만 사용자 요청에 따라 업로드하지 않음)
    if not video_id:
        # video_id가 없으면 에러 반환 (업로드를 하지 않도록 수정)
        raise HTTPException(status_code=400, detail="video_id가 필요합니다. 이미 업로드된 동영상의 video_id를 제공해주세요.")

    try:
        # summarize_video 파라미터 준비 (Form으로 받은 모든 값 전달)
        summarize_params = build_summarize_params(
            video_id=video_id,
            chunk_duration=chunk_duration,
            model=model,
            prompt=prompt,
            cs_prompt=csprompt,
            sa_prompt=saprompt,
            num_frames_per_chunk=num_frames_per_chunk,
            frame_width=frame_width,
            frame_height=frame_height,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
            max_new_tokens=max_tokens,
            seed=seed,
            batch_size=batch_size,
            rag_batch_size=rag_batch_size,
            rag_top_k=rag_top_k,
            summarize_top_p=summary_top_p,
            summarize_temperature=summary_temperature,
            summarize_max_tokens=summary_max_tokens,
            chat_top_p=chat_top_p,
            chat_temperature=chat_temperature,
            chat_max_tokens=chat_max_tokens,
            notification_top_p=alert_top_p,
            notification_temperature=alert_temperature,
            notification_max_tokens=alert_max_tokens,
            enable_audio=enable_audio
        )
        from utils.helpers import vss_client
        from utils.helpers import vss_client
        result = await vss_client.summarize_video(*summarize_params)
        return {"summary": result, "video_id": video_id}
    except HTTPException:
        # HTTPException은 그대로 전파
        raise
    except Exception as e:
        # 기타 예외 처리
        logger.error(f"vss_summarize 실행 중 오류: {e}")
        error_msg = str(e)
        
        # GStreamer 관련 에러인 경우 더 명확한 메시지 제공
        if "gst-stream-error" in error_msg or "qtdemux" in error_msg or "not-negotiated" in error_msg:
            raise HTTPException(
                status_code=500,
                detail=f"기술적 오류: {error_msg}"
            )
        else:
            raise HTTPException(status_code=500, detail=f"요약 생성 중 오류가 발생했습니다: {error_msg}")

@router.post("/save-summary")
async def save_summary(request: SaveSummaryRequest):
    """요약 결과를 DB에 저장"""
    try:
        video_id = request.video_id
        user_id = request.user_id
        prompt = request.prompt
        summary_text = request.summary_text
        
        verify_user_exists(user_id)
        
        validate_video_ownership(video_id, user_id, via_video_id=True)
        
        # 공통 저장 함수 사용
        # vss_summaries 테이블 구조:
        # - VIDEO_ID (VARCHAR): VIA 서버의 video_id (vss_videos.VIDEO_ID 컬럼 값)
        # - USER_ID (VARCHAR): 사용자 ID
        # - SUMMARY_TEXT (LONGTEXT): 요약 텍스트
        # - PROMPT (TEXT): 사용된 프롬프트
        # - CREATED_AT (TIMESTAMP): 자동 설정
        # - UPDATED_AT (TIMESTAMP): 자동 설정
        summary_id = _save_summary_to_db(video_id, user_id, summary_text, prompt)
        return {
            "success": True,
            "summary_id": summary_id,
            "message": "요약 결과가 저장되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 결과 저장 중 오류가 발생했습니다: {str(e)}")

@router.get("/summaries/{video_id}")
async def get_summary(video_id: str, user_id: str = Query(...)):
    """특정 동영상의 요약 결과 조회"""
    try:
        verify_user_exists(user_id)
        
        # 요약 결과 조회 (소유권 확인 포함)
        ensure_db_connection()
        cursor.execute(
            """SELECT s.ID, s.SUMMARY_TEXT, s.PROMPT, s.CREATED_AT, s.UPDATED_AT
               FROM vss_summaries s
               INNER JOIN vss_videos v ON s.VIDEO_ID = v.VIDEO_ID
               WHERE s.VIDEO_ID = ? AND s.USER_ID = ? AND v.USER_ID = ?""",
            (video_id, user_id, user_id)
        )
        row = cursor.fetchone()
        
        if not row:
            return {
                "success": False,
                "message": "요약 결과를 찾을 수 없습니다."
            }
        
        return {
            "success": True,
            "summary": {
                "id": row[0],
                "summary_text": row[1],
                "prompt": row[2] if len(row) > 2 else None,
                "created_at": row[3].isoformat() if len(row) > 3 and row[3] else None,
                "updated_at": row[4].isoformat() if len(row) > 4 and row[4] else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 결과 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/summaries")
async def get_user_summaries(user_id: str = Query(...)):
    """사용자의 모든 요약 결과 조회"""
    try:
        verify_user_exists(user_id)
        
        # 사용자의 모든 요약 결과 조회
        ensure_db_connection()
        cursor.execute(
            """SELECT s.ID, s.VIDEO_ID, s.SUMMARY_TEXT, s.CREATED_AT, s.UPDATED_AT, v.FILE_NAME
               FROM vss_summaries s
               INNER JOIN vss_videos v ON s.VIDEO_ID = v.VIDEO_ID
               WHERE s.USER_ID = ? AND v.USER_ID = ?
               ORDER BY s.CREATED_AT DESC""",
            (user_id, user_id)
        )
        rows = cursor.fetchall()
        
        summaries = []
        for row in rows:
            summaries.append({
                "id": row[0],
                "video_id": row[1],
                "summary_text": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "updated_at": row[4].isoformat() if row[4] else None,
                "video_name": row[5]
            })
        
        return {
            "success": True,
            "summaries": summaries,
            "count": len(summaries)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 결과 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/summaries")
async def delete_summaries(request: DeleteSummaryRequest):
    """선택된 동영상들의 요약 결과 삭제"""
    try:
        user_id = request.user_id
        video_ids = request.video_ids
        
        if not video_ids or len(video_ids) == 0:
            raise HTTPException(status_code=400, detail="동영상 ID 목록이 필요합니다.")
        
        verify_user_exists(user_id)
        
        # 선택된 동영상들의 VIDEO_ID (VIA 서버의 video_id) 조회
        ensure_db_connection()
        placeholders = ','.join(['?'] * len(video_ids))
        cursor.execute(
            f"SELECT VIDEO_ID FROM vss_videos WHERE ID IN ({placeholders}) AND USER_ID = ?",
            (*video_ids, user_id)
        )
        rows = cursor.fetchall()
        via_video_ids = [row[0] for row in rows if row[0]]  # None이 아닌 것만
        
        if not via_video_ids:
            return {
                "success": True,
                "message": "삭제할 요약 결과가 없습니다.",
                "deleted_count": 0
            }
        
        # 요약 결과 삭제
        via_placeholders = ','.join(['?'] * len(via_video_ids))
        cursor.execute(
            f"DELETE FROM vss_summaries WHERE VIDEO_ID IN ({via_placeholders}) AND USER_ID = ?",
            (*via_video_ids, user_id)
        )
        conn.commit()
        deleted_count = cursor.rowcount
        
        logger.info(f"요약 결과 삭제 완료: USER_ID={user_id}, 삭제된 요약 수={deleted_count}")

        if deleted_count <= 0:
            return {
                "success": False,
                "message": "삭제할 요약 결과가 없습니다.",
                "deleted_count": 0
            }
        
        return {
            "success": True,
            "message": f"{deleted_count}개의 요약 결과가 삭제되었습니다.",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 결과 삭제 중 오류가 발생했습니다: {str(e)}")

