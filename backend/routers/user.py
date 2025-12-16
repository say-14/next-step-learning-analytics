"""
사용자 레벨 추정 API 라우터
"""
from fastapi import APIRouter, Query
from typing import Optional

from models.user_schemas import (
    UserLevelRequest, UserLevelResponse, UserLevel,
    JobRole, EducationLevel, BasicConcept
)
from services.user_level_estimator import UserLevelEstimator

router = APIRouter()

# 추정기 인스턴스 (규칙 기반 기본)
_estimator = UserLevelEstimator(use_ml=False)
_ml_estimator = None  # ML 버전은 lazy loading


def _get_ml_estimator():
    """ML 추정기 지연 로딩"""
    global _ml_estimator
    if _ml_estimator is None:
        _ml_estimator = UserLevelEstimator(use_ml=True)
    return _ml_estimator


@router.post("/estimate-level", response_model=UserLevelResponse)
async def estimate_user_level(
    request: UserLevelRequest,
    use_ml: bool = Query(default=False, description="ML 모델 사용 여부")
):
    """
    사용자 레벨 자동 추정

    입력값:
    - education: 학력/전공 (high_school, college, university_non_cs, university_cs, graduate, bootcamp)
    - daily_study_hours: 하루 공부 가능 시간
    - known_concepts: 알고 있는 기초 개념들 (variable, loop, function, http, database, git, algorithm, oop)
    - desired_role: 희망 직무 (backend, frontend, data, ai, fullstack, devops)
    - has_project_experience: 프로젝트 경험 유무
    - coding_months: 코딩 경험 개월 수

    출력값:
    - estimated_level: 추정된 레벨
    - confidence_score: 신뢰도
    - recommended_path: 추천 학습 경로
    - strengths: 강점
    - areas_to_improve: 개선 필요 영역
    """
    estimator = _get_ml_estimator() if use_ml else _estimator
    return estimator.estimate_level(request)


@router.get("/level-options")
async def get_level_options():
    """레벨 추정에 사용 가능한 옵션 목록"""
    return {
        "education_levels": [
            {"value": e.value, "label": {
                "high_school": "고등학교 졸업",
                "college": "전문대 졸업",
                "university_non_cs": "4년제 (비전공)",
                "university_cs": "4년제 (CS/IT 전공)",
                "graduate": "대학원",
                "bootcamp": "부트캠프 수료"
            }.get(e.value, e.value)}
            for e in EducationLevel
        ],
        "job_roles": [
            {"value": j.value, "label": {
                "backend": "백엔드 개발",
                "frontend": "프론트엔드 개발",
                "data": "데이터 분석/사이언스",
                "ai": "AI/머신러닝",
                "fullstack": "풀스택 개발",
                "devops": "DevOps/인프라"
            }.get(j.value, j.value)}
            for j in JobRole
        ],
        "basic_concepts": [
            {"value": c.value, "label": {
                "variable": "변수와 데이터 타입",
                "loop": "반복문 (for, while)",
                "function": "함수",
                "http": "HTTP/웹 기초",
                "database": "데이터베이스/SQL",
                "git": "Git 버전 관리",
                "algorithm": "알고리즘 기초",
                "oop": "객체지향 프로그래밍"
            }.get(c.value, c.value)}
            for c in BasicConcept
        ],
        "user_levels": [
            {"value": l.value, "label": {
                "absolute_beginner": "완전 초보",
                "beginner": "초보",
                "junior_ready": "신입 준비 완료",
                "data_focused": "데이터 특화",
                "web_focused": "웹 개발 특화",
                "ai_focused": "AI 특화",
                "intermediate": "중급"
            }.get(l.value, l.value)}
            for l in UserLevel
        ]
    }


@router.get("/sample-estimation")
async def sample_estimation():
    """샘플 레벨 추정 (테스트용)"""
    # 다양한 샘플 케이스
    samples = [
        {
            "name": "완전 초보자",
            "request": UserLevelRequest(
                education=EducationLevel.HIGH_SCHOOL,
                daily_study_hours=2,
                known_concepts=[],
                desired_role=JobRole.BACKEND,
                has_project_experience=False,
                coding_months=0
            )
        },
        {
            "name": "부트캠프 수료 예정",
            "request": UserLevelRequest(
                education=EducationLevel.BOOTCAMP,
                daily_study_hours=8,
                known_concepts=[
                    BasicConcept.VARIABLE, BasicConcept.LOOP,
                    BasicConcept.FUNCTION, BasicConcept.HTTP,
                    BasicConcept.GIT
                ],
                desired_role=JobRole.FRONTEND,
                has_project_experience=True,
                coding_months=4
            )
        },
        {
            "name": "CS 전공 취준생",
            "request": UserLevelRequest(
                education=EducationLevel.UNIVERSITY_CS,
                daily_study_hours=5,
                known_concepts=[
                    BasicConcept.VARIABLE, BasicConcept.LOOP,
                    BasicConcept.FUNCTION, BasicConcept.HTTP,
                    BasicConcept.DATABASE, BasicConcept.GIT,
                    BasicConcept.ALGORITHM, BasicConcept.OOP
                ],
                desired_role=JobRole.BACKEND,
                has_project_experience=True,
                coding_months=24
            )
        },
        {
            "name": "데이터 분석 전환자",
            "request": UserLevelRequest(
                education=EducationLevel.UNIVERSITY_NON_CS,
                daily_study_hours=3,
                known_concepts=[
                    BasicConcept.VARIABLE, BasicConcept.LOOP,
                    BasicConcept.DATABASE
                ],
                desired_role=JobRole.DATA,
                has_project_experience=False,
                coding_months=6
            )
        }
    ]

    results = []
    for sample in samples:
        result = _estimator.estimate_level(sample["request"])
        results.append({
            "name": sample["name"],
            "input": sample["request"].model_dump(),
            "result": result.model_dump()
        })

    return {"samples": results}
