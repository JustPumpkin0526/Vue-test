-- VSS 회원 정보 테이블 생성 SQL
-- MariaDB/MySQL용

-- 기존 테이블이 있다면 삭제 (주의: 데이터가 모두 삭제됩니다)
-- DROP TABLE IF EXISTS vss_user;

-- vss_user 테이블 생성
CREATE TABLE IF NOT EXISTS vss_user (
    -- 사용자 ID (Primary Key)
    ID VARCHAR(50) NOT NULL PRIMARY KEY COMMENT '사용자 고유 ID',
    
    -- 비밀번호 (bcrypt 해시값 저장)
    -- bcrypt 해시는 정확히 60자리 문자열
    PW VARCHAR(60) NOT NULL COMMENT 'bcrypt로 해시화된 비밀번호',
    
    -- 이메일 주소 (고유값, 인덱스 추가)
    EMAIL VARCHAR(255) NOT NULL UNIQUE COMMENT '사용자 이메일 주소',
    
    -- 생성일시 (선택사항 - 추적용)
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '계정 생성일시',
    
    -- 수정일시 (선택사항 - 추적용)
    UPDATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '계정 정보 수정일시'
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='VSS 회원 정보 테이블';

-- 이메일 컬럼에 인덱스 추가 (검색 성능 향상)
CREATE INDEX idx_email ON vss_user(EMAIL);

-- 테이블 구조 확인
-- DESCRIBE vss_user;
-- 또는
-- SHOW CREATE TABLE vss_user;

