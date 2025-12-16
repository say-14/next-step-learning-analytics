"""
PostgreSQL 테이블 모델 정의 (SQLAlchemy ORM)

ERD 설계:
- users: 사용자 정보
- courses: 강의 정보
- enrollments: 수강 신청 (users - courses M:N)
- learning_logs: 학습 로그 (핵심 테이블)
- dropout_analysis: 이탈 분석 결과 (집계 테이블)
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
import enum

Base = declarative_base()


# ============ ENUM 정의 ============

class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseCategory(str, enum.Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    DATABASE = "database"
    WEB_FRONTEND = "web_frontend"
    WEB_BACKEND = "web_backend"
    DATA_ANALYSIS = "data_analysis"
    MACHINE_LEARNING = "machine_learning"
    DEVOPS = "devops"
    ALGORITHM = "algorithm"


class UserLevel(str, enum.Enum):
    ABSOLUTE_BEGINNER = "absolute_beginner"
    BEGINNER = "beginner"
    JUNIOR_READY = "junior_ready"
    INTERMEDIATE = "intermediate"


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"


# ============ 테이블 정의 ============

class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_code = Column(String(50), unique=True, nullable=False, index=True)  # 외부 식별자
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    level = Column(String(50), default="beginner")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    learning_logs = relationship("LearningLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Course(Base):
    """강의 테이블"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=False, default="beginner")
    duration_minutes = Column(Integer, nullable=False)  # 총 강의 시간(분)
    instructor = Column(String(100))
    price = Column(Integer, default=0)
    tags = Column(JSONB, default=list)  # PostgreSQL JSONB
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    learning_logs = relationship("LearningLog", back_populates="course", cascade="all, delete-orphan")
    dropout_analyses = relationship("DropoutAnalysis", back_populates="course", cascade="all, delete-orphan")

    # 인덱스
    __table_args__ = (
        Index('idx_course_category', 'category'),
        Index('idx_course_difficulty', 'difficulty'),
    )

    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}')>"


class Enrollment(Base):
    """수강 신청 테이블 (User-Course M:N 관계)"""
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="active")  # active, completed, dropped
    progress_percent = Column(Float, default=0.0)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    dropped_at = Column(DateTime, nullable=True)

    # 관계 설정
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

    # 복합 인덱스 & 제약조건
    __table_args__ = (
        Index('idx_enrollment_user_course', 'user_id', 'course_id', unique=True),
        Index('idx_enrollment_status', 'status'),
        CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='check_progress_range'),
    )

    def __repr__(self):
        return f"<Enrollment(user_id={self.user_id}, course_id={self.course_id}, status='{self.status}')>"


class LearningLog(Base):
    """학습 로그 테이블 (핵심 데이터)"""
    __tablename__ = "learning_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)

    # 학습 데이터
    progress_percent = Column(Float, nullable=False)  # 진도율 (0~100)
    watch_duration_sec = Column(Integer, nullable=False)  # 시청 시간(초)
    session_id = Column(String(100))  # 세션 식별자

    # 이탈 관련
    is_dropout = Column(Boolean, default=False)
    dropout_reason = Column(String(255), nullable=True)

    # 메타데이터
    logged_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 관계 설정
    user = relationship("User", back_populates="learning_logs")
    course = relationship("Course", back_populates="learning_logs")

    # 성능 최적화를 위한 인덱스
    __table_args__ = (
        Index('idx_log_user_course', 'user_id', 'course_id'),
        Index('idx_log_course_progress', 'course_id', 'progress_percent'),
        Index('idx_log_dropout', 'course_id', 'is_dropout'),
        Index('idx_log_logged_at', 'logged_at'),
        CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='check_log_progress_range'),
        CheckConstraint('watch_duration_sec >= 0', name='check_watch_duration_positive'),
    )

    def __repr__(self):
        return f"<LearningLog(user={self.user_id}, course={self.course_id}, progress={self.progress_percent}%)>"


class DropoutAnalysis(Base):
    """이탈 분석 집계 테이블 (구간별 분석 결과 저장)"""
    __tablename__ = "dropout_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)

    # 구간 정보 (0-10, 10-20, ... 90-100)
    segment_start = Column(Integer, nullable=False)
    segment_end = Column(Integer, nullable=False)

    # 집계 데이터
    total_users_reached = Column(Integer, default=0)  # 해당 구간 도달 사용자
    dropout_count = Column(Integer, default=0)  # 해당 구간 이탈자
    dropout_rate = Column(Float, default=0.0)  # 이탈률
    risk_level = Column(String(20))  # low, medium, high, critical

    # 분석 시점
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # 관계 설정
    course = relationship("Course", back_populates="dropout_analyses")

    __table_args__ = (
        Index('idx_analysis_course_segment', 'course_id', 'segment_start'),
    )

    def __repr__(self):
        return f"<DropoutAnalysis(course={self.course_id}, segment={self.segment_start}-{self.segment_end}, rate={self.dropout_rate}%)>"
