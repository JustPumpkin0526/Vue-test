/**
 * API 설정 파일
 * 환경 변수를 통해 API 엔드포인트를 관리합니다.
 * 
 * 사용법:
 *   import apiConfig from '@/config/api';
 *   const response = await fetch(`${apiConfig.endpoints.videos}?user_id=...`);
 */

// 환경 변수에서 API 기본 URL 가져오기
// Vercel 배포 시: Vercel 환경 변수에서 설정
// 로컬 개발 시: .env.local 파일 또는 기본값 사용
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const apiConfig = {
  baseURL: API_BASE_URL,
  endpoints: {
    // 인증
    login: `${API_BASE_URL}/login`,
    register: `${API_BASE_URL}/register`,
    sendVerificationCode: `${API_BASE_URL}/send-verification-code`,
    verifyEmailCode: `${API_BASE_URL}/verify-email-code`,
    sendResetPasswordCode: `${API_BASE_URL}/send-reset-password-code`,
    verifyResetPasswordCode: `${API_BASE_URL}/verify-reset-password-code`,
    resetPassword: `${API_BASE_URL}/reset-password`,
    
    // 동영상 관리
    uploadVideo: `${API_BASE_URL}/upload-video`,
    getVideos: `${API_BASE_URL}/videos`,
    deleteVideo: `${API_BASE_URL}/videos`,  // DELETE /videos/{video_id}
    
    // 요약 및 검색
    summarize: `${API_BASE_URL}/vss-summarize`,
    query: `${API_BASE_URL}/vss-query`,
    generateClips: `${API_BASE_URL}/generate-clips`,
    
    // 요약 결과 저장
    saveSummary: `${API_BASE_URL}/save-summary`,
    getSummary: `${API_BASE_URL}/summaries`,  // GET /summaries/{video_id}
    getUserSummaries: `${API_BASE_URL}/summaries`,  // GET /summaries
    
    // 기타
    getRecommendedChunkSize: `${API_BASE_URL}/get-recommended-chunk-size`,
    removeMedia: `${API_BASE_URL}/remove-media`,
    deleteClips: `${API_BASE_URL}/delete-clips`,
  },
  
  // 헬퍼 함수
  getVideoUrl: (videoId) => `${apiConfig.endpoints.deleteVideo}/${videoId}`,
  getSummaryUrl: (videoId) => `${apiConfig.endpoints.getSummary}/${videoId}`,
};

export default apiConfig;

