"""보고서 관련 라우터"""
import json
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from database.connection import conn, cursor, ensure_db_connection, verify_user_exists

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== 요청 모델 ====================
class CreateReportRequest(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = None
    content: str
    word_count: int = 0
    video_ids: Optional[List[int]] = None
    video_titles: Optional[List[str]] = None

class CreateReportResponse(BaseModel):
    success: bool
    report_id: Optional[int] = None
    message: str

# ==================== 엔드포인트 ====================
@router.post("/reports", response_model=CreateReportResponse)
async def create_report(request: CreateReportRequest):
    """보고서 생성"""
    try:
        user_id = request.user_id
        title = request.title
        description = request.description or ""
        content = request.content
        word_count = request.word_count or 0
        video_ids = request.video_ids or []
        video_titles = request.video_titles or []
        
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        if not title:
            raise HTTPException(status_code=400, detail="보고서 제목이 필요합니다.")
        if not content:
            raise HTTPException(status_code=400, detail="보고서 내용이 필요합니다.")
        
        verify_user_exists(user_id)
        
        ensure_db_connection()
        
        # 보고서 저장
        video_ids_json = json.dumps(video_ids) if video_ids else None
        video_titles_json = json.dumps(video_titles) if video_titles else None
        
        cursor.execute("""
            INSERT INTO vss_reports (USER_ID, TITLE, DESCRIPTION, CONTENT, WORD_COUNT, VIDEO_IDS, VIDEO_TITLES)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, description, content, word_count, video_ids_json, video_titles_json))
        conn.commit()
        
        report_id = cursor.lastrowid
        
        logger.info(f"보고서 생성 완료: USER_ID={user_id}, REPORT_ID={report_id}, TITLE={title}")
        
        return {
            "success": True,
            "report_id": report_id,
            "message": "보고서가 성공적으로 생성되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보고서 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/reports")
async def get_reports(
    user_id: str = Query(..., description="사용자 ID"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수")
):
    """보고서 목록 조회 (페이지네이션 지원)"""
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        verify_user_exists(user_id)
        
        ensure_db_connection()
        
        # vss_reports 테이블이 없으면 빈 목록 반환
        try:
            cursor.execute("SELECT COUNT(*) FROM vss_reports WHERE USER_ID = ?", (user_id,))
        except Exception as e:
            # 테이블이 없으면 빈 목록 반환
            logger.warning(f"vss_reports 테이블이 없습니다: {e}")
            return {
                "success": True,
                "reports": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "pages": 0
            }
        
        # 전체 개수 조회
        cursor.execute("SELECT COUNT(*) FROM vss_reports WHERE USER_ID = ?", (user_id,))
        total = cursor.fetchone()[0]
        
        # 페이지네이션 계산
        offset = (page - 1) * page_size
        pages = max(1, (total + page_size - 1) // page_size)
        
        # 보고서 목록 조회 (최신순)
        cursor.execute("""
            SELECT ID, TITLE, DESCRIPTION, CONTENT, WORD_COUNT, VIDEO_IDS, VIDEO_TITLES, CREATED_AT, UPDATED_AT
            FROM vss_reports
            WHERE USER_ID = ?
            ORDER BY CREATED_AT DESC
            LIMIT ? OFFSET ?
        """, (user_id, page_size, offset))
        
        rows = cursor.fetchall()
        
        reports = []
        for row in rows:
            report_id, title, description, content, word_count, video_ids_json, video_titles_json, created_at, updated_at = row
            
            # JSON 문자열 파싱
            video_ids = json.loads(video_ids_json) if video_ids_json else []
            video_titles = json.loads(video_titles_json) if video_titles_json else []
            
            reports.append({
                "id": report_id,
                "report_id": report_id,
                "title": title,
                "description": description or "",
                "content": content or "",
                "word_count": word_count or 0,
                "video_ids": video_ids,
                "video_titles": video_titles,
                "created_at": created_at.isoformat() if created_at else None,
                "createdAt": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None
            })
        
        logger.info(f"보고서 목록 조회 완료: USER_ID={user_id}, 총 {total}개, 페이지 {page}/{pages}")
        
        return {
            "success": True,
            "reports": reports,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보고서 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    user_id: str = Query(..., description="사용자 ID")
):
    """보고서 상세 조회"""
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        verify_user_exists(user_id)
        
        ensure_db_connection()
        
        # 보고서 조회
        cursor.execute("""
            SELECT ID, TITLE, DESCRIPTION, CONTENT, WORD_COUNT, VIDEO_IDS, VIDEO_TITLES, CREATED_AT, UPDATED_AT
            FROM vss_reports
            WHERE ID = ? AND USER_ID = ?
        """, (report_id, user_id))
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
        
        report_id_db, title, description, content, word_count, video_ids_json, video_titles_json, created_at, updated_at = row
        
        # JSON 문자열 파싱
        video_ids = json.loads(video_ids_json) if video_ids_json else []
        video_titles = json.loads(video_titles_json) if video_titles_json else []
        
        return {
            "success": True,
            "report": {
                "id": report_id_db,
                "report_id": report_id_db,
                "title": title,
                "description": description or "",
                "content": content or "",
                "word_count": word_count or 0,
                "video_ids": video_ids,
                "video_titles": video_titles,
                "created_at": created_at.isoformat() if created_at else None,
                "createdAt": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보고서 상세 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    user_id: str = Query(..., description="사용자 ID")
):
    """보고서 삭제"""
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        verify_user_exists(user_id)
        
        ensure_db_connection()
        
        # 보고서 소유권 확인 및 삭제
        cursor.execute("""
            DELETE FROM vss_reports
            WHERE ID = ? AND USER_ID = ?
        """, (report_id, user_id))
        conn.commit()
        
        deleted_count = cursor.rowcount
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="보고서를 찾을 수 없거나 권한이 없습니다.")
        
        logger.info(f"보고서 삭제 완료: USER_ID={user_id}, REPORT_ID={report_id}")
        
        return {
            "success": True,
            "message": "보고서가 성공적으로 삭제되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보고서 삭제 중 오류가 발생했습니다: {str(e)}")

