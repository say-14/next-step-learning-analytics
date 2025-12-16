"""
강의 상세 분석 관련 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class DifficultyLevel(str, Enum):
    """난이도"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseCategory(str, Enum):
    """강의 카테고리"""
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


class CourseInfo(BaseModel):
    """강의 기본 정보"""
    course_id: str
    title: str
    category: CourseCategory
    difficulty: DifficultyLevel
    duration_hours: float = Field(..., description="총 강의 시간")
    instructor: str
    price: int = 0
    tags: list[str] = []
    created_at: Optional[datetime] = None


class EnrollmentMetrics(BaseModel):
    """수강 관련 지표"""
    total_enrollments: int = Field(..., description="총 수강신청자 수")
    active_learners: int = Field(..., description="현재 수강 중인 학습자")
    watched_at_least_once: int = Field(..., description="1회 이상 시청자")
    watched_at_least_once_rate: float = Field(..., description="1회 이상 시청률 (%)")


class ProgressMetrics(BaseModel):
    """진도 관련 지표"""
    reached_25_percent: int = Field(..., description="25% 이상 진도")
    reached_50_percent: int = Field(..., description="50% 이상 진도")
    reached_75_percent: int = Field(..., description="75% 이상 진도")
    completed: int = Field(..., description="완강자 수")

    reached_25_rate: float = Field(..., description="25% 도달률 (%)")
    reached_50_rate: float = Field(..., description="50% 도달률 (%)")
    reached_75_rate: float = Field(..., description="75% 도달률 (%)")
    completion_rate: float = Field(..., description="완강률 (%)")


class DropoutMetrics(BaseModel):
    """이탈 관련 지표"""
    total_dropouts: int = Field(..., description="총 이탈자 수")
    dropout_rate: float = Field(..., description="이탈률 (%)")
    average_dropout_point: float = Field(..., description="평균 이탈 지점 (%)")
    peak_dropout_segment: str = Field(..., description="최다 이탈 구간")
    peak_dropout_rate: float = Field(..., description="최다 이탈 구간 이탈률 (%)")


class EngagementMetrics(BaseModel):
    """참여도 지표"""
    average_watch_time_minutes: float = Field(..., description="평균 시청 시간 (분)")
    average_sessions_per_user: float = Field(..., description="사용자당 평균 세션 수")
    average_days_to_complete: float = Field(..., description="완강까지 평균 소요일")
    rewatch_rate: float = Field(..., description="재시청률 (%)")


class CourseDetailAnalysis(BaseModel):
    """강의 상세 분석 결과"""
    course_info: CourseInfo
    enrollment_metrics: EnrollmentMetrics
    progress_metrics: ProgressMetrics
    dropout_metrics: DropoutMetrics
    engagement_metrics: EngagementMetrics
    funnel_data: list[dict]  # 퍼널 분석 데이터
    comparison_with_average: dict  # 평균 대비 비교


class CourseSummaryCard(BaseModel):
    """강의 요약 카드 (목록용)"""
    course_id: str
    title: str
    category: str
    difficulty: str
    total_enrollments: int
    completion_rate: float
    average_rating: float = 0.0
    dropout_rate: float
    is_popular: bool = False
    is_recommended: bool = False
