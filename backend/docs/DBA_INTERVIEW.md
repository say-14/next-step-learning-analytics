# DBA 면접 답변 가이드

> 이 프로젝트 기반 예상 질문 및 답변

---

## 1. 프로젝트 소개

**Q: 이 프로젝트에 대해 설명해주세요.**

> 온라인 교육 플랫폼의 **학습자 이탈 패턴 분석 시스템**입니다.
>
> - 500명 이상의 사용자, 12개 강의, 수만 건의 학습 로그 데이터를 PostgreSQL로 관리
> - 구간별(0-10%, 10-20%, ...) 이탈률을 분석하여 위험 구간을 식별
> - FastAPI + React로 실시간 대시보드 제공

---

## 2. 데이터베이스 설계

**Q: ERD를 설명해주세요.**

```
users (1) ──< (N) enrollments (N) >── (1) courses
                      │
                      │ 1:N
                      ▼
               learning_logs
                      │
                      │ 집계
                      ▼
             dropout_analyses
```

| 테이블 | 설명 | 예상 데이터량 |
|--------|------|---------------|
| users | 사용자 정보 | 수천~수만 |
| courses | 강의 정보 | 수십~수백 |
| enrollments | 수강 신청 (M:N) | 수만 |
| learning_logs | 학습 로그 (**핵심**) | 수십만~수백만 |
| dropout_analyses | 분석 결과 (집계) | 강의수 × 10 |

**Q: 왜 이렇게 설계했나요?**

> 1. **정규화**: users, courses를 분리하여 중복 최소화
> 2. **M:N 관계**: enrollments로 다대다 관계 해소
> 3. **집계 테이블 분리**: dropout_analyses로 반복 계산 방지
> 4. **JSONB 활용**: courses.tags에 유연한 태그 저장

---

## 3. 인덱스 전략

**Q: 어떤 인덱스를 만들었고, 왜 그렇게 했나요?**

```sql
-- 1. 학습 로그 분석용 (가장 중요!)
CREATE INDEX idx_logs_course_progress
ON learning_logs(course_id, progress_percent);

-- 2. 이탈 로그 필터링 (부분 인덱스)
CREATE INDEX idx_logs_dropout
ON learning_logs(course_id, is_dropout)
WHERE is_dropout = TRUE;

-- 3. 시계열 조회
CREATE INDEX idx_logs_logged_at ON learning_logs(logged_at);
```

> **설계 이유:**
> - `(course_id, progress_percent)`: 강의별 구간 분석 쿼리에서 사용
> - **부분 인덱스**: 이탈 로그만 인덱싱하여 인덱스 크기 감소 (전체의 ~30%)
> - 시계열 인덱스: 일별/주별 추이 분석용

**Q: 인덱스가 잘 사용되는지 어떻게 확인했나요?**

```sql
EXPLAIN ANALYZE
SELECT * FROM learning_logs
WHERE course_id = 1 AND progress_percent BETWEEN 0 AND 10;
```

> `Index Scan using idx_logs_course_progress`가 나오면 정상 사용

---

## 4. 쿼리 최적화

**Q: 가장 복잡한 쿼리를 설명해주세요.**

```sql
-- 구간별 이탈 분석 (CTE + Window 함수)
WITH segment_data AS (
    SELECT
        course_id,
        FLOOR(progress_percent / 10) * 10 AS segment_start,
        COUNT(*) FILTER (WHERE is_dropout = true) AS dropout_count
    FROM learning_logs
    WHERE course_id = :course_id
    GROUP BY course_id, FLOOR(progress_percent / 10)
),
user_max_progress AS (
    SELECT user_id, MAX(progress_percent) AS max_progress
    FROM learning_logs
    WHERE course_id = :course_id
    GROUP BY user_id
)
SELECT
    sd.segment_start,
    sd.dropout_count,
    ROUND((sd.dropout_count::numeric / rc.users_reached) * 100, 2) AS dropout_rate
FROM segment_data sd
LEFT JOIN reached_counts rc ON sd.segment_start = rc.segment_start
ORDER BY sd.segment_start;
```

> **핵심 기법:**
> - **CTE (WITH)**: 복잡한 쿼리를 단계별로 분리
> - **FILTER 절**: CASE WHEN 대신 가독성 향상
> - **FLOOR 함수**: 0-10, 10-20 등 구간 그룹핑

**Q: 이 쿼리를 어떻게 최적화했나요?**

> 1. `idx_logs_course_progress` 인덱스 활용
> 2. 집계 결과를 `dropout_analyses` 테이블에 캐싱
> 3. 분석 시점 기록으로 필요시에만 재계산

---

## 5. PostgreSQL 고급 기능

**Q: PostgreSQL의 어떤 기능을 활용했나요?**

| 기능 | 사용 위치 | 설명 |
|------|-----------|------|
| **JSONB** | courses.tags | 유연한 태그 저장, GIN 인덱스 가능 |
| **부분 인덱스** | idx_logs_dropout | 이탈 로그만 인덱싱 |
| **FILTER 절** | 집계 쿼리 | 조건부 COUNT |
| **generate_series** | 구간 생성 | 0-90까지 10단위 시퀀스 |
| **PL/pgSQL 함수** | analyze_course_dropout() | 재사용 가능한 분석 로직 |

**Q: JSONB를 왜 선택했나요?**

> - 태그는 개수/종류가 가변적
> - 배열 형태로 저장하면서도 인덱스 검색 가능
> - `tags @> '["인기"]'`로 특정 태그 검색 가능

---

## 6. 성능 모니터링

**Q: 슬로우 쿼리는 어떻게 찾나요?**

```sql
-- pg_stat_statements 활용
SELECT
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Q: 테이블 상태는 어떻게 확인하나요?**

```sql
-- 테이블 통계
SELECT
    relname,
    n_live_tup,    -- 라이브 행 수
    n_dead_tup,    -- 데드 튜플 (VACUUM 필요)
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public';
```

---

## 7. 트러블슈팅 경험

**Q: 성능 문제를 해결한 경험이 있나요?**

> **문제**: 학습 로그 테이블이 커지면서 분석 쿼리가 느려짐
>
> **원인 분석**:
> ```sql
> EXPLAIN ANALYZE SELECT ... -- Seq Scan 발견
> ```
>
> **해결**:
> 1. 복합 인덱스 `(course_id, progress_percent)` 추가
> 2. 분석 결과를 별도 테이블에 캐싱
> 3. 실행 시간 3초 → 50ms로 개선

---

## 8. 확장성 고려

**Q: 데이터가 더 커지면 어떻게 대응하나요?**

> 1. **파티셔닝**: learning_logs를 월별로 파티션
>    ```sql
>    CREATE TABLE learning_logs_2024_01 PARTITION OF learning_logs
>    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
>    ```
>
> 2. **읽기 복제본**: 분석 쿼리는 읽기 전용 복제본으로
>
> 3. **집계 테이블**: dropout_analyses처럼 미리 계산된 결과 활용

---

## 9. 백업/복구

**Q: 백업 전략은 어떻게 세우나요?**

> - **일일 백업**: pg_dump로 전체 백업
> - **WAL 아카이빙**: 시점 복구(PITR) 가능하도록
> - **테스트**: 정기적으로 복구 테스트 수행

```bash
# 백업
pg_dump -Fc education_db > backup_$(date +%Y%m%d).dump

# 복구
pg_restore -d education_db backup_20241213.dump
```

---

## 10. ORM vs Raw SQL

**Q: ORM을 사용했는데, Raw SQL도 쓰셨네요?**

> **ORM (SQLAlchemy)**: 단순 CRUD, 안전한 파라미터 바인딩
>
> **Raw SQL**: 복잡한 집계, Window 함수, CTE
>
> ```python
> # ORM - 단순 조회
> db.query(Course).filter(Course.id == 1).first()
>
> # Raw SQL - 복잡한 분석
> db.execute(text("""
>     WITH segment_data AS (...)
>     SELECT ...
> """), {"course_id": 1})
> ```
>
> **DBA 관점**: Raw SQL을 직접 작성하면서 실행 계획을 확인하고 최적화할 수 있음

---

## 추가 어필 포인트

1. **데이터 무결성**: CHECK 제약조건으로 0-100% 범위 강제
2. **Cascade 삭제**: 참조 무결성 유지하면서 연관 데이터 자동 삭제
3. **View 활용**: 복잡한 집계를 v_course_summary로 캡슐화
4. **시드 데이터**: 재현 가능한 테스트 데이터 생성 (seed=42)

---

## 프로젝트에서 보여주기

```bash
# 1. PostgreSQL 접속
psql -U postgres -d education_db

# 2. 테이블 확인
\dt

# 3. 인덱스 확인
\di

# 4. 분석 쿼리 실행
SELECT * FROM v_course_summary ORDER BY dropout_rate DESC;

# 5. 실행 계획 확인
EXPLAIN ANALYZE SELECT * FROM analyze_course_dropout(1);
```
