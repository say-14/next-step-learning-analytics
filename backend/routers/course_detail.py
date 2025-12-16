"""
강의 상세 분석 API 라우터
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from models.course_schemas import (
    CourseDetailAnalysis, CourseSummaryCard,
    CourseCategory, DifficultyLevel
)
from services.course_analyzer import CourseAnalyzer

router = APIRouter()

# 분석기 인스턴스
_analyzer = CourseAnalyzer(seed=42)


@router.get("/", response_model=list[CourseSummaryCard])
async def get_all_courses(
    category: Optional[CourseCategory] = Query(default=None, description="카테고리 필터"),
    difficulty: Optional[DifficultyLevel] = Query(default=None, description="난이도 필터"),
    sort_by: str = Query(default="enrollments", description="정렬 기준 (enrollments, completion_rate, dropout_rate)")
):
    """
    전체 강의 목록 조회

    - category: 카테고리로 필터링
    - difficulty: 난이도로 필터링
    - sort_by: 정렬 기준
    """
    courses = _analyzer.get_all_courses_summary()

    # 필터링
    if category:
        courses = [c for c in courses if c.category == category.value]

    if difficulty:
        courses = [c for c in courses if c.difficulty == difficulty.value]

    # 정렬
    if sort_by == "completion_rate":
        courses = sorted(courses, key=lambda x: x.completion_rate, reverse=True)
    elif sort_by == "dropout_rate":
        courses = sorted(courses, key=lambda x: x.dropout_rate, reverse=False)
    else:  # enrollments (기본)
        courses = sorted(courses, key=lambda x: x.total_enrollments, reverse=True)

    return courses


@router.get("/detail/{course_id}", response_model=CourseDetailAnalysis)
async def get_course_detail(course_id: str):
    """
    강의 상세 분석 조회

    **지표 포함:**
    - 수강 지표: 총 수강신청자, 1회 이상 시청자
    - 진도 지표: 25%/50%/75%/완강 도달률
    - 이탈 지표: 총 이탈자, 평균 이탈 지점, 최다 이탈 구간
    - 참여도 지표: 평균 시청 시간, 평균 세션 수
    - 퍼널 데이터: 단계별 전환율
    - 평균 대비 비교
    """
    detail = _analyzer.get_course_detail(course_id)

    if not detail:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")

    return detail


@router.get("/detail/{course_id}/funnel")
async def get_course_funnel(course_id: str):
    """강의 퍼널(전환율) 데이터만 조회"""
    detail = _analyzer.get_course_detail(course_id)

    if not detail:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")

    return {
        "course_id": course_id,
        "title": detail.course_info.title,
        "funnel": detail.funnel_data
    }


@router.get("/detail/{course_id}/metrics")
async def get_course_metrics(course_id: str):
    """
    강의 핵심 지표 요약

    수강신청 대비 핵심 지표만 간단하게 반환
    """
    detail = _analyzer.get_course_detail(course_id)

    if not detail:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")

    return {
        "course_id": course_id,
        "title": detail.course_info.title,
        "metrics": {
            "total_enrollments": detail.enrollment_metrics.total_enrollments,
            "watched_once": detail.enrollment_metrics.watched_at_least_once,
            "watched_once_rate": detail.enrollment_metrics.watched_at_least_once_rate,
            "reached_50_percent": detail.progress_metrics.reached_50_percent,
            "reached_50_rate": detail.progress_metrics.reached_50_rate,
            "completed": detail.progress_metrics.completed,
            "completion_rate": detail.progress_metrics.completion_rate,
            "average_dropout_point": detail.dropout_metrics.average_dropout_point
        },
        "summary": f"수강신청자 {detail.enrollment_metrics.total_enrollments}명 중 "
                   f"{detail.enrollment_metrics.watched_at_least_once}명이 1회 이상 시청, "
                   f"{detail.progress_metrics.reached_50_percent}명이 50% 진도 달성, "
                   f"{detail.progress_metrics.completed}명 완강 "
                   f"(평균 이탈 구간: {detail.dropout_metrics.average_dropout_point}%)"
    }


@router.get("/top-completion", response_model=list[CourseSummaryCard])
async def get_top_completion_courses(
    limit: int = Query(default=5, ge=1, le=20, description="조회할 강의 수")
):
    """완강률 TOP N 강의"""
    return _analyzer.get_top_completion_courses(limit)


@router.get("/compare-funnel")
async def compare_course_funnels(
    course_ids: str = Query(..., description="비교할 강의 ID들 (쉼표로 구분)")
):
    """
    여러 강의의 퍼널 비교

    예: /api/courses/compare-funnel?course_ids=course_001,course_002,course_003
    """
    ids = [cid.strip() for cid in course_ids.split(",")]

    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="최소 2개 이상의 강의 ID가 필요합니다")

    if len(ids) > 5:
        raise HTTPException(status_code=400, detail="최대 5개까지 비교 가능합니다")

    comparison = _analyzer.get_funnel_comparison(ids)

    return {
        "comparison": comparison,
        "stages": ["enrolled", "watched", "25%", "50%", "75%", "completed"]
    }


@router.get("/categories")
async def get_categories():
    """사용 가능한 카테고리 목록"""
    return {
        "categories": [
            {"value": c.value, "label": {
                "python": "Python",
                "javascript": "JavaScript",
                "java": "Java",
                "database": "데이터베이스",
                "web_frontend": "웹 프론트엔드",
                "web_backend": "웹 백엔드",
                "data_analysis": "데이터 분석",
                "machine_learning": "머신러닝",
                "devops": "DevOps",
                "algorithm": "알고리즘"
            }.get(c.value, c.value)}
            for c in CourseCategory
        ]
    }


@router.get("/difficulties")
async def get_difficulties():
    """사용 가능한 난이도 목록"""
    return {
        "difficulties": [
            {"value": d.value, "label": {
                "beginner": "초급",
                "intermediate": "중급",
                "advanced": "고급"
            }.get(d.value, d.value)}
            for d in DifficultyLevel
        ]
    }
