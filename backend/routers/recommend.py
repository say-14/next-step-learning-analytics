"""
개인화 추천 API 라우터
"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from models.user_schemas import (
    UserProfile, UserLevel, JobRole, BasicConcept
)
from services.recommender import CourseRecommender
from services.course_analyzer import CourseAnalyzer

router = APIRouter()

# 서비스 인스턴스
_course_analyzer = CourseAnalyzer(seed=42)
_recommender = CourseRecommender(course_analyzer=_course_analyzer, seed=42)


class RecommendRequest(BaseModel):
    """추천 요청"""
    user_id: str = Field(..., description="사용자 ID")
    level: UserLevel = Field(..., description="사용자 레벨")
    desired_role: JobRole = Field(..., description="희망 직무")
    known_concepts: list[BasicConcept] = Field(default=[], description="알고 있는 개념")
    completed_courses: list[str] = Field(default=[], description="완료한 강의 ID 목록")
    in_progress_courses: list[str] = Field(default=[], description="수강 중인 강의 ID 목록")


class QuickRecommendRequest(BaseModel):
    """간단 추천 요청 (레벨 추정 없이)"""
    desired_role: JobRole = Field(..., description="희망 직무")
    experience_level: str = Field(
        default="beginner",
        description="경험 수준 (beginner, intermediate, advanced)"
    )
    completed_courses: list[str] = Field(default=[], description="완료한 강의 ID 목록")


@router.post("/personalized")
async def get_personalized_recommendations(
    request: RecommendRequest,
    limit: int = Query(default=5, ge=1, le=20, description="추천 개수"),
    method: str = Query(
        default="hybrid",
        description="추천 방식 (rule_based, collaborative, hybrid)"
    )
):
    """
    개인화 강의 추천

    **추천 방식:**
    - rule_based: 규칙 기반 (프로필 매칭)
    - collaborative: 협업 필터링 (유사 사용자 기반)
    - hybrid: 하이브리드 (둘 다 결합)

    **고려 요소:**
    - 사용자 레벨에 맞는 난이도
    - 희망 직무와 관련된 카테고리
    - 완강률이 높은 강의 우선
    - 이미 수강한 강의 제외
    """
    user_profile = UserProfile(
        user_id=request.user_id,
        level=request.level,
        desired_role=request.desired_role,
        known_concepts=request.known_concepts,
        completed_courses=request.completed_courses,
        in_progress_courses=request.in_progress_courses
    )

    if method == "rule_based":
        recommendations = _recommender.recommend_rule_based(user_profile, limit)
    elif method == "collaborative":
        if not request.completed_courses:
            raise HTTPException(
                status_code=400,
                detail="협업 필터링에는 수강 완료한 강의가 필요합니다"
            )
        recommendations = _recommender.recommend_collaborative(
            request.user_id,
            request.completed_courses,
            limit
        )
    else:  # hybrid
        recommendations = _recommender.recommend_hybrid(user_profile, limit)

    return {
        "user_id": request.user_id,
        "method": method,
        "recommendations": recommendations,
        "total_count": len(recommendations)
    }


@router.post("/quick")
async def get_quick_recommendations(
    request: QuickRecommendRequest,
    limit: int = Query(default=5, ge=1, le=10, description="추천 개수")
):
    """
    간단 추천 (레벨 추정 없이 직무/경험만으로)

    빠른 추천이 필요할 때 사용
    """
    # 경험 수준을 UserLevel로 매핑
    level_map = {
        "beginner": UserLevel.BEGINNER,
        "intermediate": UserLevel.JUNIOR_READY,
        "advanced": UserLevel.INTERMEDIATE
    }
    level = level_map.get(request.experience_level, UserLevel.BEGINNER)

    user_profile = UserProfile(
        user_id="quick_user",
        level=level,
        desired_role=request.desired_role,
        known_concepts=[],
        completed_courses=request.completed_courses,
        in_progress_courses=[]
    )

    recommendations = _recommender.recommend_rule_based(user_profile, limit)

    return {
        "desired_role": request.desired_role.value,
        "experience_level": request.experience_level,
        "recommendations": recommendations
    }


@router.post("/learning-path")
async def get_learning_path(request: RecommendRequest):
    """
    맞춤 학습 경로 추천

    레벨과 직무에 따른 단계별 강의 추천
    초급 → 중급 → 고급 순서로 학습 로드맵 제공
    """
    user_profile = UserProfile(
        user_id=request.user_id,
        level=request.level,
        desired_role=request.desired_role,
        known_concepts=request.known_concepts,
        completed_courses=request.completed_courses,
        in_progress_courses=request.in_progress_courses
    )

    path = _recommender.get_personalized_path(user_profile)

    return {
        "user_id": request.user_id,
        "desired_role": request.desired_role.value,
        "current_level": request.level.value,
        "learning_path": path,
        "total_stages": len(path)
    }


@router.get("/by-role/{role}")
async def get_recommendations_by_role(
    role: JobRole,
    limit: int = Query(default=5, ge=1, le=10)
):
    """
    직무별 추천 강의

    특정 직무에 적합한 강의 목록 (로그인 없이도 사용 가능)
    """
    # 임시 프로필 생성
    temp_profile = UserProfile(
        user_id="anonymous",
        level=UserLevel.BEGINNER,
        desired_role=role,
        known_concepts=[],
        completed_courses=[],
        in_progress_courses=[]
    )

    recommendations = _recommender.recommend_rule_based(temp_profile, limit)

    return {
        "role": role.value,
        "role_name": {
            "backend": "백엔드 개발",
            "frontend": "프론트엔드 개발",
            "data": "데이터 분석",
            "ai": "AI/머신러닝",
            "fullstack": "풀스택 개발",
            "devops": "DevOps"
        }.get(role.value, role.value),
        "recommendations": recommendations
    }


@router.get("/by-level/{level}")
async def get_recommendations_by_level(
    level: UserLevel,
    limit: int = Query(default=5, ge=1, le=10)
):
    """
    레벨별 추천 강의

    특정 레벨에 적합한 강의 목록
    """
    # 레벨에 맞는 난이도의 강의 필터링
    all_courses = _course_analyzer.get_all_courses_summary()

    level_difficulty_map = {
        UserLevel.ABSOLUTE_BEGINNER: ["beginner"],
        UserLevel.BEGINNER: ["beginner"],
        UserLevel.JUNIOR_READY: ["intermediate", "advanced"],
        UserLevel.DATA_FOCUSED: ["beginner", "intermediate"],
        UserLevel.WEB_FOCUSED: ["beginner", "intermediate"],
        UserLevel.AI_FOCUSED: ["intermediate", "advanced"],
        UserLevel.INTERMEDIATE: ["intermediate", "advanced"],
    }

    allowed_difficulties = level_difficulty_map.get(level, ["beginner", "intermediate"])

    filtered = [
        c for c in all_courses
        if c.difficulty in allowed_difficulties
    ]

    # 완강률 높은 순 정렬
    sorted_courses = sorted(filtered, key=lambda x: x.completion_rate, reverse=True)

    return {
        "level": level.value,
        "level_name": {
            "absolute_beginner": "완전 초보",
            "beginner": "초보",
            "junior_ready": "신입 준비 완료",
            "data_focused": "데이터 특화",
            "web_focused": "웹 개발 특화",
            "ai_focused": "AI 특화",
            "intermediate": "중급"
        }.get(level.value, level.value),
        "recommended_difficulties": allowed_difficulties,
        "courses": [
            {
                "course_id": c.course_id,
                "title": c.title,
                "category": c.category,
                "difficulty": c.difficulty,
                "completion_rate": c.completion_rate,
                "total_enrollments": c.total_enrollments
            }
            for c in sorted_courses[:limit]
        ]
    }


@router.get("/similar/{course_id}")
async def get_similar_courses(
    course_id: str,
    limit: int = Query(default=5, ge=1, le=10)
):
    """
    유사 강의 추천

    특정 강의와 유사한 강의 목록 (협업 필터링 기반)
    """
    recommendations = _recommender.recommend_collaborative(
        user_id="anonymous",
        completed_courses=[course_id],
        limit=limit
    )

    if not recommendations:
        # 폴백: 같은 카테고리 강의 추천
        all_courses = _course_analyzer.get_all_courses_summary()
        target_course = next((c for c in all_courses if c.course_id == course_id), None)

        if target_course:
            similar = [
                c for c in all_courses
                if c.category == target_course.category and c.course_id != course_id
            ]
            recommendations = [
                {
                    "course_id": c.course_id,
                    "title": c.title,
                    "category": c.category,
                    "difficulty": c.difficulty,
                    "completion_rate": c.completion_rate,
                    "reason": "같은 카테고리 강의",
                    "method": "category_based"
                }
                for c in sorted(similar, key=lambda x: x.completion_rate, reverse=True)[:limit]
            ]

    return {
        "base_course_id": course_id,
        "similar_courses": recommendations
    }


@router.get("/popular")
async def get_popular_courses(
    limit: int = Query(default=5, ge=1, le=20)
):
    """
    인기 강의 추천

    수강신청자 수 기준 인기 강의
    """
    all_courses = _course_analyzer.get_all_courses_summary()
    popular = sorted(all_courses, key=lambda x: x.total_enrollments, reverse=True)

    return {
        "criteria": "enrollments",
        "courses": [
            {
                "course_id": c.course_id,
                "title": c.title,
                "category": c.category,
                "difficulty": c.difficulty,
                "total_enrollments": c.total_enrollments,
                "completion_rate": c.completion_rate
            }
            for c in popular[:limit]
        ]
    }


@router.get("/high-completion")
async def get_high_completion_courses(
    limit: int = Query(default=5, ge=1, le=20),
    min_enrollments: int = Query(default=100, description="최소 수강신청자 수")
):
    """
    완강률 높은 강의 추천

    수강생이 일정 수 이상이면서 완강률이 높은 강의
    """
    all_courses = _course_analyzer.get_all_courses_summary()

    # 최소 수강자 필터
    filtered = [c for c in all_courses if c.total_enrollments >= min_enrollments]

    # 완강률 순 정렬
    high_completion = sorted(filtered, key=lambda x: x.completion_rate, reverse=True)

    return {
        "criteria": "completion_rate",
        "min_enrollments": min_enrollments,
        "courses": [
            {
                "course_id": c.course_id,
                "title": c.title,
                "category": c.category,
                "difficulty": c.difficulty,
                "total_enrollments": c.total_enrollments,
                "completion_rate": c.completion_rate,
                "dropout_rate": c.dropout_rate
            }
            for c in high_completion[:limit]
        ]
    }
