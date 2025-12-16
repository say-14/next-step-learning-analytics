"""
학습 로그 데이터 모델 정의
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LearningLog(BaseModel):
    """개별 학습 로그"""
    user_id: str
    course_id: str
    timestamp: datetime
    progress_percent: float  # 0~100
    watch_duration_sec: int  # 시청 시간(초)
    is_dropout: bool = False  # 이탈 여부


class DropoutPoint(BaseModel):
    """이탈 지점 정보"""
    user_id: str
    course_id: str
    dropout_percent: float  # 이탈한 진도율
    dropout_time: datetime


class SegmentAnalysis(BaseModel):
    """구간별 분석 결과"""
    segment_start: int  # 구간 시작 (0, 10, 20, ...)
    segment_end: int    # 구간 끝 (10, 20, 30, ...)
    dropout_count: int  # 해당 구간 이탈자 수
    dropout_rate: float # 이탈률 (%)
    risk_level: str     # 'low', 'medium', 'high', 'critical'


class CourseDropoutReport(BaseModel):
    """강의별 이탈 분석 리포트"""
    course_id: str
    course_title: str
    total_enrollments: int
    total_dropouts: int
    overall_dropout_rate: float
    completion_rate: float
    segments: list[SegmentAnalysis]
    danger_zones: list[dict]  # 위험 구간 정보
