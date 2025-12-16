-- ============================================================
-- Education DB 초기화 스크립트
-- PostgreSQL 16+
-- DBA 포트폴리오: 테이블 설계, 인덱스 전략, 제약조건
-- ============================================================

-- 데이터베이스 생성 (psql에서 실행)
-- CREATE DATABASE education_db;

-- ============================================================
-- 1. 테이블 생성
-- ============================================================

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_code VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    level VARCHAR(50) DEFAULT 'beginner',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 강의 테이블
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'beginner',
    duration_minutes INTEGER NOT NULL,
    instructor VARCHAR(100),
    price INTEGER DEFAULT 0,
    tags JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 수강 신청 테이블 (M:N 관계)
CREATE TABLE IF NOT EXISTS enrollments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, dropped
    progress_percent FLOAT DEFAULT 0.0,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    dropped_at TIMESTAMP,
    CONSTRAINT check_progress_range CHECK (progress_percent >= 0 AND progress_percent <= 100),
    CONSTRAINT unique_user_course UNIQUE (user_id, course_id)
);

-- 학습 로그 테이블 (핵심 데이터)
CREATE TABLE IF NOT EXISTS learning_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    progress_percent FLOAT NOT NULL,
    watch_duration_sec INTEGER NOT NULL,
    session_id VARCHAR(100),
    is_dropout BOOLEAN DEFAULT FALSE,
    dropout_reason VARCHAR(255),
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_log_progress_range CHECK (progress_percent >= 0 AND progress_percent <= 100),
    CONSTRAINT check_watch_duration_positive CHECK (watch_duration_sec >= 0)
);

-- 이탈 분석 테이블 (집계 결과)
CREATE TABLE IF NOT EXISTS dropout_analyses (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    segment_start INTEGER NOT NULL,
    segment_end INTEGER NOT NULL,
    total_users_reached INTEGER DEFAULT 0,
    dropout_count INTEGER DEFAULT 0,
    dropout_rate FLOAT DEFAULT 0.0,
    risk_level VARCHAR(20),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. 인덱스 생성 (성능 최적화)
-- ============================================================

-- 사용자 조회 최적화
CREATE INDEX IF NOT EXISTS idx_users_user_code ON users(user_code);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 강의 필터링 최적화
CREATE INDEX IF NOT EXISTS idx_courses_category ON courses(category);
CREATE INDEX IF NOT EXISTS idx_courses_difficulty ON courses(difficulty);
CREATE INDEX IF NOT EXISTS idx_courses_active ON courses(is_active) WHERE is_active = TRUE;

-- 수강 현황 조회 최적화
CREATE INDEX IF NOT EXISTS idx_enrollments_user ON enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments(status);

-- 학습 로그 분석 최적화 (핵심!)
CREATE INDEX IF NOT EXISTS idx_logs_user_course ON learning_logs(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_logs_course_progress ON learning_logs(course_id, progress_percent);
CREATE INDEX IF NOT EXISTS idx_logs_dropout ON learning_logs(course_id, is_dropout) WHERE is_dropout = TRUE;
CREATE INDEX IF NOT EXISTS idx_logs_logged_at ON learning_logs(logged_at);

-- 이탈 분석 조회 최적화
CREATE INDEX IF NOT EXISTS idx_analysis_course_segment ON dropout_analyses(course_id, segment_start);


-- ============================================================
-- 3. 유용한 뷰 생성
-- ============================================================

-- 강의별 요약 통계 뷰
CREATE OR REPLACE VIEW v_course_summary AS
SELECT
    c.id AS course_id,
    c.course_code,
    c.title,
    c.category,
    c.difficulty,
    COUNT(DISTINCT e.user_id) AS total_enrollments,
    COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.user_id END) AS completions,
    COUNT(DISTINCT CASE WHEN e.status = 'dropped' THEN e.user_id END) AS dropouts,
    COUNT(DISTINCT CASE WHEN e.status = 'active' THEN e.user_id END) AS active_learners,
    ROUND(
        COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.user_id END)::numeric
        / NULLIF(COUNT(DISTINCT e.user_id), 0) * 100, 2
    ) AS completion_rate,
    ROUND(
        COUNT(DISTINCT CASE WHEN e.status = 'dropped' THEN e.user_id END)::numeric
        / NULLIF(COUNT(DISTINCT e.user_id), 0) * 100, 2
    ) AS dropout_rate
FROM courses c
LEFT JOIN enrollments e ON c.id = e.course_id
WHERE c.is_active = TRUE
GROUP BY c.id, c.course_code, c.title, c.category, c.difficulty;


-- 구간별 이탈 분석 뷰
CREATE OR REPLACE VIEW v_dropout_by_segment AS
SELECT
    c.course_code,
    c.title,
    FLOOR(l.progress_percent / 10) * 10 AS segment_start,
    FLOOR(l.progress_percent / 10) * 10 + 10 AS segment_end,
    COUNT(*) AS total_logs,
    COUNT(*) FILTER (WHERE l.is_dropout = TRUE) AS dropout_count,
    ROUND(
        COUNT(*) FILTER (WHERE l.is_dropout = TRUE)::numeric / COUNT(*) * 100, 2
    ) AS dropout_rate
FROM courses c
JOIN learning_logs l ON c.id = l.course_id
GROUP BY c.course_code, c.title, FLOOR(l.progress_percent / 10)
ORDER BY c.course_code, segment_start;


-- ============================================================
-- 4. 유용한 함수/프로시저
-- ============================================================

-- 구간별 이탈 분석 함수
CREATE OR REPLACE FUNCTION analyze_course_dropout(p_course_id INTEGER)
RETURNS TABLE (
    segment_start INTEGER,
    segment_end INTEGER,
    users_reached BIGINT,
    dropout_count BIGINT,
    dropout_rate NUMERIC,
    risk_level VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH user_max_progress AS (
        SELECT
            user_id,
            MAX(progress_percent) AS max_progress
        FROM learning_logs
        WHERE course_id = p_course_id
        GROUP BY user_id
    ),
    segments AS (
        SELECT generate_series(0, 90, 10) AS seg_start
    ),
    segment_analysis AS (
        SELECT
            s.seg_start,
            s.seg_start + 10 AS seg_end,
            COUNT(DISTINCT u.user_id) AS users_reached,
            COUNT(DISTINCT CASE
                WHEN l.is_dropout = TRUE
                AND l.progress_percent >= s.seg_start
                AND l.progress_percent < s.seg_start + 10
                THEN l.user_id
            END) AS dropouts
        FROM segments s
        LEFT JOIN user_max_progress u ON u.max_progress >= s.seg_start
        LEFT JOIN learning_logs l ON l.user_id = u.user_id AND l.course_id = p_course_id
        GROUP BY s.seg_start
    )
    SELECT
        sa.seg_start::INTEGER,
        sa.seg_end::INTEGER,
        sa.users_reached,
        sa.dropouts,
        ROUND(sa.dropouts::numeric / NULLIF(sa.users_reached, 0) * 100, 2),
        CASE
            WHEN sa.dropouts::numeric / NULLIF(sa.users_reached, 0) * 100 >= 20 THEN 'critical'
            WHEN sa.dropouts::numeric / NULLIF(sa.users_reached, 0) * 100 >= 15 THEN 'high'
            WHEN sa.dropouts::numeric / NULLIF(sa.users_reached, 0) * 100 >= 10 THEN 'medium'
            ELSE 'low'
        END::VARCHAR
    FROM segment_analysis sa
    ORDER BY sa.seg_start;
END;
$$ LANGUAGE plpgsql;


-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER trigger_courses_updated_at
    BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- 5. 샘플 쿼리 (DBA 면접용)
-- ============================================================

-- Q1. 가장 이탈률이 높은 강의 TOP 5
-- SELECT * FROM v_course_summary ORDER BY dropout_rate DESC LIMIT 5;

-- Q2. 특정 강의의 구간별 이탈 분석
-- SELECT * FROM analyze_course_dropout(1);

-- Q3. 위험 구간(critical) 보유 강의 조회
-- SELECT DISTINCT c.title, da.segment_start, da.dropout_rate
-- FROM dropout_analyses da
-- JOIN courses c ON da.course_id = c.id
-- WHERE da.risk_level = 'critical';

-- Q4. 일별 학습 활동 추이 (시계열)
-- SELECT DATE(logged_at) AS date, COUNT(*) AS log_count
-- FROM learning_logs
-- GROUP BY DATE(logged_at)
-- ORDER BY date DESC;

-- Q5. 사용자별 완강률 상위 10명
-- SELECT u.username, COUNT(*) FILTER (WHERE e.status = 'completed') AS completions
-- FROM users u
-- JOIN enrollments e ON u.id = e.user_id
-- GROUP BY u.id, u.username
-- ORDER BY completions DESC
-- LIMIT 10;
