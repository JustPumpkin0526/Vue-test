"""동영상 관련 유틸리티 함수"""
import os
import re
import time
import shutil
import logging
from pathlib import Path
from moviepy.video.io.VideoFileClip import VideoFileClip
from database.connection import conn, cursor, ensure_db_connection
from config.settings import (
    VIA_SERVER_URL, CLIP_CLEANUP_AGE, CONVERTED_VIDEOS_DIR, UNSUPPORTED_VIDEO_FORMATS
)

logger = logging.getLogger(__name__)

def parse_timestamps(timestamp_text, video_duration):
    """
    타임스탬프 텍스트에서 시간 구간을 파싱하여 (start_time, end_time) 튜플 리스트를 반환합니다.
    
    지원 형식:
    - 초 단위: 10.5, 120.3
    - 분:초 형식: 1:30, 2:45
    - 범위: 10.5-15.3, 1:30-2:45, 10.5~15.3
    - 여러 타임스탬프: "10.5, 20.3, 30.1" 또는 "1:30, 2:45"
    
    타임스탬프는 짝으로 처리되며, 첫 번째 타임스탬프가 시작 시간, 두 번째 타임스탬프가 끝 시간이 됩니다.
    타임스탬프가 명시적으로 주어진 경우 실제 범위를 그대로 사용합니다.
    
    Args:
        timestamp_text (str): 타임스탬프가 포함된 텍스트
        video_duration (float): 동영상 전체 길이 (초)
    
    Returns:
        List[tuple]: [(start_time, end_time), ...] 리스트. 타임스탬프가 명시된 경우 실제 범위를 사용.
    """
    if not timestamp_text or not isinstance(timestamp_text, str):
        return []
    
    timestamps = []
    
    # 분:초 형식을 초로 변환하는 함수
    def parse_time_to_seconds(time_str):
        time_str = time_str.strip()
        # 분:초 형식인지 확인
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                try:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
                except ValueError:
                    return None
        # 초 단위 형식
        try:
            return float(time_str)
        except ValueError:
            return None
    
    # 타임스탬프 텍스트에서 숫자와 범위 패턴 찾기
    # 패턴: 숫자(초 또는 분:초) 또는 범위(숫자-숫자, 숫자~숫자)
    
    # 1. 범위 패턴 찾기 (예: 10.5-15.3, 1:30-2:45)
    range_pattern = r'(\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)?)\s*[-~]\s*(\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)?)'
    range_timestamps = []
    for match in re.finditer(range_pattern, timestamp_text):
        start_str = match.group(1)
        end_str = match.group(2)
        start_time = parse_time_to_seconds(start_str)
        end_time = parse_time_to_seconds(end_str)
        if start_time is not None and end_time is not None:
            start_time = max(0, min(start_time, video_duration))
            end_time = max(start_time, min(end_time, video_duration))
            # 범위 패턴으로 명시된 경우 실제 범위를 그대로 사용 (15초 제한 없음)
            range_timestamps.append((start_time, end_time))
    
    # 2. 단일 타임스탬프 찾기 (범위에 포함되지 않은 것들)
    # 이미 범위로 처리된 부분을 제외하고 나머지에서 찾기
    processed_text = re.sub(range_pattern, '', timestamp_text)
    
    # 숫자 패턴 찾기 (초 단위 또는 분:초)
    number_pattern = r'\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)?'
    single_timestamps = []
    for match in re.finditer(number_pattern, processed_text):
        time_str = match.group(0)
        time_seconds = parse_time_to_seconds(time_str)
        if time_seconds is not None:
            time_seconds = max(0, min(time_seconds, video_duration))
            single_timestamps.append(time_seconds)
    
    # 범위 패턴으로 찾은 타임스탬프는 그대로 사용
    timestamps.extend(range_timestamps)
    
    # 단일 타임스탬프는 짝으로 묶어서 처리
    # 첫 번째 타임스탬프가 시작 시간, 두 번째 타임스탬프가 끝 시간
    for i in range(0, len(single_timestamps) - 1, 2):
        start_time = single_timestamps[i]
        end_time = single_timestamps[i + 1]
        # 타임스탬프가 짝으로 명시된 경우 실제 범위를 그대로 사용 (15초 제한 없음)
        timestamps.append((start_time, end_time))
    
    # 중복 제거 및 정렬
    timestamps = sorted(set(timestamps), key=lambda x: x[0])
    
    # 겹치는 구간 병합 (5초 이내로 가까운 구간)
    merged = []
    for start, end in timestamps:
        if merged and start - merged[-1][1] < 5:
            # 이전 구간과 가까우면 병합 (실제 범위 유지)
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            # 실제 범위를 그대로 사용
            merged.append((start, end))
    
    logger.info(f"파싱된 타임스탬프: {merged}")
    return merged

def convert_video_to_mp4(input_path: str, output_path: str):
    """동영상을 MP4 형식으로 변환"""
    try:
        video = VideoFileClip(str(input_path))
        # MP4로 변환 (H.264 코덱 사용)
        video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        video.close()
        logger.info(f"동영상 변환 완료: {input_path} -> {output_path}")
        return True
    except Exception as e:
        logger.error(f"동영상 변환 실패: {e}")
        if 'video' in locals():
            try:
                video.close()
            except:
                pass
        return False

def extract_video_metadata(file_path: str, video_id: int, filename: str):
    """동영상 메타데이터를 추출하여 DB에 업데이트"""
    try:
        video = VideoFileClip(str(file_path))
        width = int(video.w) if video.w else None
        height = int(video.h) if video.h else None
        duration = float(video.duration) if video.duration else None
        video.close()
        
        # 메타데이터 업데이트
        ensure_db_connection()
        cursor.execute(
            """UPDATE vss_videos 
               SET WIDTH = ?, HEIGHT = ?, DURATION = ? 
               WHERE ID = ?""",
            (width, height, duration, video_id)
        )
        conn.commit()
        logger.info(f"동영상 메타데이터 업데이트 완료: {filename} (ID: {video_id})")
    except Exception as e:
        logger.warning(f"동영상 메타데이터 추출 실패: {e}")

