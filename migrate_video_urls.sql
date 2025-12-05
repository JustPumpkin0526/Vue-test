-- migrate_video_urls.sql
-- 기존 /videos/ 경로를 /video-files/ 경로로 업데이트하는 마이그레이션 스크립트

-- FILE_URL이 /videos/로 시작하는 경우 /video-files/로 변경
UPDATE vss_videos 
SET FILE_URL = REPLACE(FILE_URL, '/videos/', '/video-files/')
WHERE FILE_URL LIKE '/videos/%';

-- 변경된 레코드 수 확인
SELECT COUNT(*) as updated_count 
FROM vss_videos 
WHERE FILE_URL LIKE '/video-files/%';

