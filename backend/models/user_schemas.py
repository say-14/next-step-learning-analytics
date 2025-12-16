"""
사용자 레벨 추정 관련 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class JobRole(str, Enum):
    """희망 직무"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATA = "data"
    AI = "ai"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"


class EducationLevel(str, Enum):
    """학력"""
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    UNIVERSITY_NON_CS = "university_non_cs"
    UNIVERSITY_CS = "university_cs"
    GRADUATE = "graduate"
    BOOTCAMP = "bootcamp"


class UserLevel(str, Enum):
    """추정된 사용자 레벨"""
    ABSOLUTE_BEGINNER = "absolute_beginner"  # 완전 초보
    BEGINNER = "beginner"                    # 초보
    JUNIOR_READY = "junior_ready"            # 신입 준비
    DATA_FOCUSED = "data_focused"            # 데이터 특화
    WEB_FOCUSED = "web_focused"              # 웹 특화
    AI_FOCUSED = "ai_focused"                # AI 특화
    INTERMEDIATE = "intermediate"            # 중급


class BasicConcept(str, Enum):
    """기초 개념 체크 항목"""
    VARIABLE = "variable"           # 변수
    LOOP = "loop"                   # 반복문
    FUNCTION = "function"           # 함수
    HTTP = "http"                   # HTTP 기초
    DATABASE = "database"           # DB 기초
    GIT = "git"                     # Git 기초
    ALGORITHM = "algorithm"         # 알고리즘 기초
    OOP = "oop"                     # 객체지향 기초


class UserLevelRequest(BaseModel):
    """사용자 레벨 추정 요청"""
    education: EducationLevel = Field(..., description="학력/전공")
    daily_study_hours: float = Field(..., ge=0, le=24, description="하루 공부 가능 시간")
    known_concepts: list[BasicConcept] = Field(default=[], description="알고 있는 기초 개념들")
    desired_role: JobRole = Field(..., description="희망 직무")
    has_project_experience: bool = Field(default=False, description="프로젝트 경험 유무")
    coding_months: int = Field(default=0, ge=0, description="코딩 경험 개월 수")


class UserLevelResponse(BaseModel):
    """사용자 레벨 추정 결과"""
    estimated_level: UserLevel
    level_description: str
    confidence_score: float = Field(..., ge=0, le=1, description="신뢰도 점수")
    recommended_path: list[str]
    strengths: list[str]
    areas_to_improve: list[str]
    estimated_time_to_job_ready: str
    detail_scores: dict


class UserProfile(BaseModel):
    """사용자 프로필 (추천 시스템용)"""
    user_id: str
    level: UserLevel
    desired_role: JobRole
    known_concepts: list[BasicConcept]
    completed_courses: list[str] = []
    in_progress_courses: list[str] = []
    preferred_difficulty: str = "beginner"  # beginner, intermediate, advanced
