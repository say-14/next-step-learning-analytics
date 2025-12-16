"""
이탈 구간 분석 API 라우터 (PostgreSQL 연동)
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services.db_service import DropoutAnalysisService, CourseService
from models.db_models import Course, LearningLog, Enrollment

router = APIRouter()


@router.get("/courses")
async def get_courses(db: Session = Depends(get_db)):
    """
    분석 가능한 강의 목록 조회
    """
    summaries = DropoutAnalysisService.get_all_courses_summary(db)

    return {"courses": summaries}


@router.get("/segments/{course_id}")
async def get_segment_analysis(course_id: int, db: Session = Depends(get_db)):
    """
    특정 강의의 구간별 이탈 분석
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")

    # 분석 실행 및 저장
    analyses = DropoutAnalysisService.analyze_course(db, course_id)

    segments = [
        {
            "segment_start": a.segment_start,
            "segment_end": a.segment_end,
            "dropout_count": a.dropout_count,
            "dropout_rate": a.dropout_rate,
            "risk_level": a.risk_level,
            "total_users_reached": a.total_users_reached
        }
        for a in analyses
    ]

    return {
        "course_id": course_id,
        "course_title": course.title,
        "segments": segments
    }


@router.get("/danger-zones/{course_id}")
async def get_danger_zones(
    course_id: int,
    threshold: float = Query(default=15.0, description="위험 기준 이탈률 (%)"),
    db: Session = Depends(get_db)
):
    """
    특정 강의의 위험 구간 조회
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")

    # 분석 데이터 조회 또는 생성
    analyses = DropoutAnalysisService.analyze_course(db, course_id)

    danger_zones = [
        {
            "segment": f"{a.segment_start}-{a.segment_end}%",
            "dropout_rate": a.dropout_rate,
            "risk_level": a.risk_level,
            "dropout_count": a.dropout_count
        }
        for a in analyses
        if a.dropout_rate >= threshold
    ]

    return {
        "course_id": course_id,
        "course_title": course.title,
        "threshold": threshold,
        "danger_zones": danger_zones
    }


@router.get("/summary/{course_id}")
async def get_course_summary(course_id: int, db: Session = Depends(get_db)):
    """
    특정 강의의 전체 이탈 분석 요약
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")

    summary = DropoutAnalysisService.get_course_summary(db, course_id)

    # 구간별 분석 추가
    analyses = DropoutAnalysisService.analyze_course(db, course_id)

    # 가장 위험한 구간 찾기
    if analyses:
        worst = max(analyses, key=lambda x: x.dropout_rate)
        summary["peak_dropout_segment"] = f"{worst.segment_start}-{worst.segment_end}%"
        summary["peak_dropout_rate"] = worst.dropout_rate
    else:
        summary["peak_dropout_segment"] = "N/A"
        summary["peak_dropout_rate"] = 0

    return summary


@router.get("/chart-data/{course_id}")
async def get_chart_data(course_id: int, db: Session = Depends(get_db)):
    """
    Chart.js용 데이터 반환
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")

    analyses = DropoutAnalysisService.analyze_course(db, course_id)

    labels = [f"{a.segment_start}-{a.segment_end}%" for a in analyses]
    dropout_rates = [a.dropout_rate for a in analyses]
    dropout_counts = [a.dropout_count for a in analyses]

    # 색상 결정
    colors = []
    for a in analyses:
        if a.risk_level == "critical":
            colors.append("rgba(220, 53, 69, 0.8)")  # 빨강
        elif a.risk_level == "high":
            colors.append("rgba(255, 193, 7, 0.8)")  # 노랑
        elif a.risk_level == "medium":
            colors.append("rgba(23, 162, 184, 0.8)")  # 파랑
        else:
            colors.append("rgba(40, 167, 69, 0.8)")  # 초록

    return {
        "course_id": course_id,
        "course_title": course.title,
        "labels": labels,
        "datasets": [
            {
                "label": "이탈률 (%)",
                "data": dropout_rates,
                "backgroundColor": colors
            }
        ],
        "dropout_counts": dropout_counts
    }


@router.get("/reasons/{course_id}")
async def get_dropout_reasons(course_id: int, db: Session = Depends(get_db)):
    """
    특정 강의의 이탈 사유 분석
    """
    from sqlalchemy import func, text

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")

    # 이탈 사유별 집계
    result = db.query(
        LearningLog.dropout_reason,
        func.count(LearningLog.id).label("count")
    ).filter(
        LearningLog.course_id == course_id,
        LearningLog.is_dropout == True,
        LearningLog.dropout_reason.isnot(None)
    ).group_by(
        LearningLog.dropout_reason
    ).order_by(
        func.count(LearningLog.id).desc()
    ).all()

    reasons = [
        {"reason": r.dropout_reason, "count": r.count}
        for r in result
    ]

    total_dropouts = sum(r["count"] for r in reasons)

    return {
        "course_id": course_id,
        "course_title": course.title,
        "total_dropouts": total_dropouts,
        "reasons": reasons
    }
