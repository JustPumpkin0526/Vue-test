"""VSS API 클라이언트"""
import os
import aiohttp
import logging
from fastapi import HTTPException
from utils.helpers import get_session
from config.settings import (
    VIA_MODEL_TIMEOUT,
    VIA_UPLOAD_TIMEOUT_MIN,
    VIA_UPLOAD_TIMEOUT_MAX,
    VIA_UPLOAD_TIMEOUT_PER_MB
)

logger = logging.getLogger(__name__)

class VSS:
    """Wrapper to call VSS REST APIs"""

    def __init__(self, host):
        self.host = host
        self.summarize_endpoint = self.host + "/summarize"
        self.query_endpoint = self.host + "/chat/completions"
        self.files_endpoint = self.host + "/files"
        self.models_endpoint = self.host + "/models"
        self.model = None
        self.f_count = 0

    async def check_response(self, response, json_format=True):
        logger.debug(f"Response Status Code: {response.status}")
        if response.status == 200:
            try:
                return await response.json()
            except Exception:
                logger.warning("JSON decode error, returning text.")
                return await response.text()
        else:
            text = await response.text()
            logger.error(f"서버 에러: {response.status}, {text}")
            return text

    async def get_model(self):
        session = await get_session()
        try:
            async with session.get(
                self.models_endpoint,
                timeout=aiohttp.ClientTimeout(total=VIA_MODEL_TIMEOUT)
            ) as resp:
                json_data = await self.check_response(resp)
                try:
                    return json_data["data"][0]["id"]
                except Exception as e:
                    raise HTTPException(status_code=502, detail=f"Invalid response from VIA /models: {e}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to reach VIA server for models: {e}")

    async def upload_video(self, video_path):
        session = await get_session()
        data = aiohttp.FormData()
        
        file_handle = open(video_path, "rb")
        try:
            file_size = os.path.getsize(video_path)
            logger.info(f"Uploading video file: {video_path} (size: {file_size / (1024*1024):.2f} MB)")
            
            data.add_field("file", file_handle, filename=f"file_{self.f_count}")
            data.add_field("purpose", "vision")
            data.add_field("media_type", "video")
            
            # 파일 크기에 따라 동적 타임아웃 계산
            timeout_seconds = max(
                VIA_UPLOAD_TIMEOUT_MIN,
                min(VIA_UPLOAD_TIMEOUT_MAX, int(file_size / (1024 * 1024) * VIA_UPLOAD_TIMEOUT_PER_MB))
            )

            async with session.post(
                self.files_endpoint, 
                data=data,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            ) as response:
                self.f_count += 1
                json_data = await self.check_response(response)
                return json_data.get("id")  # return uploaded file id

        finally:
            # 파일 핸들 닫기
            file_handle.close()

    async def summarize_video(self, file_id, prompt, cs_prompt, sa_prompt, chunk_duration, model, num_frames_per_chunk, frame_width, frame_height, top_k, top_p, temperature, max_new_tokens, seed, batch_size, rag_batch_size, rag_top_k, summarize_top_p, summarize_temperature, summarize_max_tokens, chat_top_p, chat_temperature, chat_max_tokens, notification_top_p, notification_temperature, notification_max_tokens, enable_audio):
        logger.info(f"prompt: {prompt}")
        body = {
            "id": file_id,
            "prompt": prompt,
            "caption_summarization_prompt": cs_prompt,
            "summary_aggregation_prompt": sa_prompt,
            "model": model,
            "chunk_duration": chunk_duration,
            "temperature": temperature,
            "seed": seed,
            "max_tokens": max_new_tokens,
            "top_p": top_p,
            "top_k": top_k,
            "num_frames_per_chunk": num_frames_per_chunk,
            "vlm_input_width": frame_width,
            "vlm_input_height": frame_height,
            "summarize_top_p": summarize_top_p,
            "summarize_temperature": summarize_temperature,
            "summarize_max_tokens": summarize_max_tokens,
            "chat_top_p": chat_top_p,
            "chat_temperature": chat_temperature,
            "chat_max_tokens": chat_max_tokens,
            "notification_top_p": notification_top_p,
            "notification_temperature": notification_temperature,
            "notification_max_tokens": notification_max_tokens,
            "summarize_batch_size": batch_size,
            "rag_batch_size": rag_batch_size,
            "rag_top_k": rag_top_k,
            "enable_chat": True,
            "enable_audio": enable_audio,
        }

        session = await get_session()
        async with session.post(self.summarize_endpoint, json=body) as response:
            # 에러 응답 처리
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"VIA 서버 summarize_video 오류 (HTTP {response.status}): {error_text}")
                
                # GStreamer 에러인 경우 더 명확한 메시지 제공
                if "gst-stream-error" in error_text or "qtdemux" in error_text or "not-negotiated" in error_text:
                    error_msg = (
                        "동영상 파일 처리 중 오류가 발생했습니다. "
                        "가능한 원인:\n"
                        "1. 손상된 동영상 파일\n"
                        "2. 지원하지 않는 코덱 또는 포맷\n"
                        "3. 파일이 완전히 업로드되지 않음\n"
                        "4. 파일 메타데이터 문제\n\n"
                        f"VIA 서버 오류: {error_text}"
                    )
                    raise HTTPException(status_code=500, detail=error_msg)
                else:
                    raise HTTPException(status_code=response.status, detail=f"VIA 서버 summarize_video 오류: {error_text}")
            
            # check response
            json_data = await self.check_response(response)
            if isinstance(json_data, dict) and "choices" in json_data:
                message_content = json_data["choices"][0]["message"]["content"]
                return message_content
            else:
                # JSON이 아니거나 에러일 때는 원본 텍스트 또는 에러 메시지 반환
                return json_data

    async def list_files(self, purpose: str = "vision"):
        """
        VIA 서버에서 파일 목록 조회
        
        Args:
            purpose: 파일 목적 (기본값: "vision")
        
        Returns:
            파일 목록 (ListFilesResponse 형식)
        """
        session = await get_session()
        try:
            async with session.get(
                self.files_endpoint,
                params={"purpose": purpose},
                timeout=aiohttp.ClientTimeout(total=VIA_MODEL_TIMEOUT)
            ) as response:
                json_data = await self.check_response(response)
                
                # 오류 응답 처리
                if response.status != 200:
                    error_msg = json_data if isinstance(json_data, str) else str(json_data)
                    raise HTTPException(status_code=response.status, detail=f"VIA 서버 파일 목록 조회 오류: {error_msg}")
                
                # 정상 응답 처리
                if isinstance(json_data, dict) and "data" in json_data:
                    return json_data
                else:
                    raise HTTPException(status_code=502, detail=f"VIA 서버 응답 형식 오류: {json_data}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"VIA 서버 파일 목록 조회 실패: {e}")
            raise HTTPException(status_code=502, detail=f"VIA 서버 파일 목록 조회 실패: {str(e)}")

    async def query_video(self, video_id, model, chunk_size, temperature, seed, max_new_tokens, top_p, top_k, query):
        body = {
            "id": video_id,
            "model": model,
            "chunk_duration": chunk_size,
            "temperature": temperature,
            "seed": seed,
            "max_tokens": max_new_tokens,
            "top_p": top_p,
            "top_k": top_k,
            "stream": True,
            "stream_options": {"include_usage": True},
            "highlight": False,
        }
        body["messages"] = [{"content": str(query), "role": "user"}]
        session = await get_session()
        async with session.post(self.query_endpoint, json=body) as response:
            json_data = await self.check_response(response)
            
            # 오류 응답 처리
            if response.status != 200:
                error_msg = json_data if isinstance(json_data, str) else str(json_data)
                raise HTTPException(status_code=response.status, detail=f"VIA 서버 query_video 오류: {error_msg}")
            
            # 정상 응답 처리
            if isinstance(json_data, dict) and "choices" in json_data:
                message_content = json_data["choices"][0]["message"]["content"]
                return message_content
            else:
                raise HTTPException(status_code=502, detail=f"VIA 서버 응답 형식 오류: {json_data}")

