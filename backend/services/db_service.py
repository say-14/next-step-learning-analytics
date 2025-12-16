"""
데이터베이스 CRUD 서비스
DBA 포트폴리오: Raw SQL과 ORM 혼용으로 유연성 확보
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from models.db_models import User, Course, Enrollment, LearningLog, DropoutAnalysis


class UserService:
    """사용자 CRUD"""

    @staticmethod
    def create(db: Session, user_code: str, username: str, email: str, level: str = "beginner") -> User:
        user = User(user_code=user_code, username=username, email=email, level=level)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_by_code(db: Session, user_code: str) -> Optional[User]:
        return db.query(User).filter(User.user_code == user_code).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()


class CourseService:
    """강의 CRUD"""

    @staticmethod
    def create(db: Session, course_code: str, title: str, category: str,
               difficulty: str, duration_minutes: int, **kwargs) -> Course:
        course = Course(
            course_code=course_code,
            title=title,
            category=category,
            difficulty=difficulty,
            duration_minutes=duration_minutes,
            **kwargs
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def get_by_code(db: Session, course_code: str) -> Optional[Course]:
        return db.query(Course).filter(Course.course_code == course_code).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Course).filter(Course.is_active == True).offset(skip).limit(limit).all()


class EnrollmentService:
    """수강 신청 CRUD"""

    @staticmethod
    def enroll(db: Session, user_id: int, course_id: int) -> Enrollment:
        enrollment = Enrollment(user_id=user_id, course_id=course_id, status="active")
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def update_progress(db: Session, user_id: int, course_id: int, progress: float):
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id
        ).first()
        if enrollment:
            enrollment.progress_percent = progress
            if progress >= 100:
                enrollment.status = "completed"
                enrollment.completed_at = datetime.utcnow()
            db.commit()
        return enrollment

    @staticmethod
    def mark_dropped(db: Session, user_id: int, course_id: int):
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id
        ).first()
        if enrollment:
            enrollment.status = "dropped"
            enrollment.dropped_at = datetime.utcnow()
            db.commit()
        return enrollment


class LearningLogService:
    """학습 로그 CRUD"""

    @staticmethod
    def create(db: Session, user_id: int, course_id: int, progress_percent: float,
               watch_duration_sec: int, is_dropout: bool = False, dropout_reason: str = None) -> LearningLog:
        log = LearningLog(
            user_id=user_id,
            course_id=course_id,
            progress_percent=progress_percent,
            watch_duration_sec=watch_duration_sec,
            is_dropout=is_dropout,
            dropout_reason=dropout_reason
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def bulk_create(db: Session, logs: list[dict]):
        """벌크 인서트 (성능 최적화)"""
        db.bulk_insert_mappings(LearningLog, logs)
        db.commit()

    @staticmethod
    def get_by_course(db: Session, course_id: int):
        return db.query(LearningLog).filter(LearningLog.course_id == course_id).all()


class DropoutAnalysisService:
    """이탈 분석 서비스 - DBA 포트폴리오 핵심!"""

    # 위험도 기준
    RISK_THRESHOLDS = {"critical": 20, "high": 15, "medium": 10, "low": 0}

    @staticmethod
    def analyze_course(db: Session, course_id: int) -> list[DropoutAnalysis]:
        """
        강의별 이탈 구간 분석 (Raw SQL 사용)
        - 구간별 이탈률 계산
        - Window 함수 활용
        """

        # Raw SQL로 구간별 이탈 분석 (DBA 역량 어필)
        sql = text("""
            WITH segment_data AS (
                SELECT
                    course_id,
                    FLOOR(progress_percent / 10) * 10 AS segment_start,
                    FLOOR(progress_percent / 10) * 10 + 10 AS segment_end,
                    COUNT(*) AS total_logs,
                    COUNT(*) FILTER (WHERE is_dropout = true) AS dropout_count
                FROM learning_logs
                WHERE course_id = :course_id
                GROUP BY course_id, FLOOR(progress_percent / 10)
            ),
            user_max_progress AS (
                SELECT
                    user_id,
                    course_id,
                    MAX(progress_percent) AS max_progress
                FROM learning_logs
                WHERE course_id = :course_id
                GROUP BY user_id, course_id
            ),
            reached_counts AS (
                SELECT
                    s.segment_start,
                    COUNT(DISTINCT u.user_id) AS users_reached
                FROM (SELECT generate_series(0, 90, 10) AS segment_start) s
                LEFT JOIN user_max_progress u ON u.max_progress >= s.segment_start
                GROUP BY s.segment_start
            )
            SELECT
                sd.course_id,
                sd.segment_start,
                sd.segment_end,
                COALESCE(rc.users_reached, 0) AS total_users_reached,
                sd.dropout_count,
                CASE
                    WHEN rc.users_reached > 0
                    THEN ROUND((sd.dropout_count::numeric / rc.users_reached) * 100, 2)
                    ELSE 0
                END AS dropout_rate
            FROM segment_data sd
            LEFT JOIN reached_counts rc ON sd.segment_start = rc.segment_start
            ORDER BY sd.segment_start
        """)

        result = db.execute(sql, {"course_id": course_id})
        analyses = []

        for row in result:
            rate = float(row.dropout_rate)
            risk = DropoutAnalysisService._get_risk_level(rate)

            analysis = DropoutAnalysis(
                course_id=course_id,
                segment_start=int(row.segment_start),
                segment_end=int(row.segment_end),
                total_users_reached=int(row.total_users_reached),
                dropout_count=int(row.dropout_count),
                dropout_rate=rate,
                risk_level=risk,
                analyzed_at=datetime.utcnow()
            )
            analyses.append(analysis)

        # 기존 분석 삭제 후 새로 저장
        db.query(DropoutAnalysis).filter(DropoutAnalysis.course_id == course_id).delete()
        db.add_all(analyses)
        db.commit()

        return analyses

    @staticmethod
    def _get_risk_level(rate: float) -> str:
        if rate >= 20:
            return "critical"
        elif rate >= 15:
            return "high"
        elif rate >= 10:
            return "medium"
        return "low"

    @staticmethod
    def get_course_summary(db: Session, course_id: int) -> dict:
        """강의 요약 통계 (집계 쿼리)"""

        sql = text("""
            SELECT
                c.id AS course_id,
                c.title,
                c.category,
                c.difficulty,
                COUNT(DISTINCT e.user_id) AS total_enrollments,
                COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.user_id END) AS completions,
                COUNT(DISTINCT CASE WHEN e.status = 'dropped' THEN e.user_id END) AS dropouts,
                ROUND(
                    COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.user_id END)::numeric
                    / NULLIF(COUNT(DISTINCT e.user_id), 0) * 100, 2
                ) AS completion_rate,
                ROUND(
                    COUNT(DISTINCT CASE WHEN e.status = 'dropped' THEN e.user_id END)::numeric
                    / NULLIF(COUNT(DISTINCT e.user_id), 0) * 100, 2
                ) AS dropout_rate,
                ROUND(AVG(e.progress_percent)::numeric, 2) AS avg_progress
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id
            WHERE c.id = :course_id
            GROUP BY c.id, c.title, c.category, c.difficulty
        """)

        result = db.execute(sql, {"course_id": course_id}).fetchone()

        if result:
            return {
                "course_id": result.course_id,
                "title": result.title,
                "category": result.category,
                "difficulty": result.difficulty,
                "total_enrollments": result.total_enrollments or 0,
                "completions": result.completions or 0,
                "dropouts": result.dropouts or 0,
                "completion_rate": float(result.completion_rate or 0),
                "overall_dropout_rate": float(result.dropout_rate or 0),
                "average_dropout_point": float(result.avg_progress or 0)
            }
        return {
            "total_enrollments": 0,
            "completion_rate": 0,
            "overall_dropout_rate": 0,
            "average_dropout_point": 0
        }

    @staticmethod
    def get_all_courses_summary(db: Session) -> list[dict]:
        """전체 강의 요약 (리스트용)"""

        sql = text("""
            WITH course_stats AS (
                SELECT
                    c.id AS course_id,
                    c.course_code,
                    c.title,
                    c.category,
                    c.difficulty,
                    COUNT(DISTINCT e.user_id) AS total_enrollments,
                    COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.user_id END) AS completions,
                    COUNT(DISTINCT CASE WHEN e.status = 'dropped' THEN e.user_id END) AS dropouts
                FROM courses c
                LEFT JOIN enrollments e ON c.id = e.course_id
                WHERE c.is_active = true
                GROUP BY c.id, c.course_code, c.title, c.category, c.difficulty
            )
            SELECT
                *,
                ROUND(completions::numeric / NULLIF(total_enrollments, 0) * 100, 2) AS completion_rate,
                ROUND(dropouts::numeric / NULLIF(total_enrollments, 0) * 100, 2) AS dropout_rate
            FROM course_stats
            ORDER BY total_enrollments DESC
        """)

        result = db.execute(sql)
        return [dict(row._mapping) for row in result]
