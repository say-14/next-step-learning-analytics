"""
강의 상세 분석 서비스
수강 행동 로그 기반 지표 계산
"""
import random
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional
import statistics

from models.course_schemas import (
    CourseInfo, CourseCategory, DifficultyLevel,
    EnrollmentMetrics, ProgressMetrics, DropoutMetrics,
    EngagementMetrics, CourseDetailAnalysis, CourseSummaryCard
)


class CourseAnalyzer:
    """강의 상세 분석기"""

    # 샘플 강의 데이터
    SAMPLE_COURSES = [
        CourseInfo(
            course_id="course_001",
            title="Python 기초 완성",
            category=CourseCategory.PYTHON,
            difficulty=DifficultyLevel.BEGINNER,
            duration_hours=20,
            instructor="김파이썬",
            price=55000,
            tags=["python", "기초", "입문"]
        ),
        CourseInfo(
            course_id="course_002",
            title="FastAPI 마스터",
            category=CourseCategory.WEB_BACKEND,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_hours=15,
            instructor="이백엔드",
            price=79000,
            tags=["fastapi", "api", "backend", "python"]
        ),
        CourseInfo(
            course_id="course_003",
            title="Django 웹 개발",
            category=CourseCategory.WEB_BACKEND,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_hours=30,
            instructor="박장고",
            price=89000,
            tags=["django", "web", "backend", "python"]
        ),
        CourseInfo(
            course_id="course_004",
            title="데이터 분석 입문",
            category=CourseCategory.DATA_ANALYSIS,
            difficulty=DifficultyLevel.BEGINNER,
            duration_hours=25,
            instructor="최데이터",
            price=65000,
            tags=["pandas", "데이터분석", "python", "시각화"]
        ),
        CourseInfo(
            course_id="course_005",
            title="머신러닝 기초",
            category=CourseCategory.MACHINE_LEARNING,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_hours=35,
            instructor="정머신",
            price=99000,
            tags=["ml", "scikit-learn", "python", "ai"]
        ),
        CourseInfo(
            course_id="course_006",
            title="React 프론트엔드",
            category=CourseCategory.WEB_FRONTEND,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_hours=28,
            instructor="강리액트",
            price=75000,
            tags=["react", "javascript", "frontend", "web"]
        ),
        CourseInfo(
            course_id="course_007",
            title="SQL 데이터베이스",
            category=CourseCategory.DATABASE,
            difficulty=DifficultyLevel.BEGINNER,
            duration_hours=18,
            instructor="윤디비",
            price=49000,
            tags=["sql", "database", "mysql", "postgresql"]
        ),
        CourseInfo(
            course_id="course_008",
            title="Docker 컨테이너",
            category=CourseCategory.DEVOPS,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_hours=12,
            instructor="신도커",
            price=59000,
            tags=["docker", "container", "devops"]
        ),
        CourseInfo(
            course_id="course_009",
            title="알고리즘 문제풀이",
            category=CourseCategory.ALGORITHM,
            difficulty=DifficultyLevel.ADVANCED,
            duration_hours=40,
            instructor="조알고",
            price=109000,
            tags=["algorithm", "코딩테스트", "자료구조"]
        ),
        CourseInfo(
            course_id="course_010",
            title="JavaScript 기초",
            category=CourseCategory.JAVASCRIPT,
            difficulty=DifficultyLevel.BEGINNER,
            duration_hours=22,
            instructor="한자스",
            price=55000,
            tags=["javascript", "기초", "web"]
        ),
    ]

    def __init__(self, seed: Optional[int] = 42):
        if seed:
            random.seed(seed)

        self.courses = {c.course_id: c for c in self.SAMPLE_COURSES}
        self._generated_metrics = {}
        self._generate_all_metrics()

    def _generate_all_metrics(self):
        """모든 강의의 지표 생성"""
        for course_id, course_info in self.courses.items():
            self._generated_metrics[course_id] = self._generate_course_metrics(course_info)

    def _generate_course_metrics(self, course_info: CourseInfo) -> dict:
        """강의 지표 랜덤 생성 (현실적인 분포)"""
        # 난이도에 따른 기본 완강률 조정
        base_completion_rate = {
            DifficultyLevel.BEGINNER: random.uniform(0.25, 0.40),
            DifficultyLevel.INTERMEDIATE: random.uniform(0.18, 0.30),
            DifficultyLevel.ADVANCED: random.uniform(0.12, 0.22),
        }.get(course_info.difficulty, 0.25)

        # 수강신청자 수 (인기도에 따라)
        total_enrollments = random.randint(500, 2500)

        # 단계별 도달률 (퍼널)
        watched_rate = random.uniform(0.75, 0.92)
        reached_25_rate = random.uniform(0.55, 0.75)
        reached_50_rate = random.uniform(0.35, 0.55)
        reached_75_rate = random.uniform(0.20, 0.40)
        completion_rate = base_completion_rate

        # 각 단계 인원 계산
        watched_at_least_once = int(total_enrollments * watched_rate)
        reached_25 = int(total_enrollments * reached_25_rate)
        reached_50 = int(total_enrollments * reached_50_rate)
        reached_75 = int(total_enrollments * reached_75_rate)
        completed = int(total_enrollments * completion_rate)

        # 이탈 지표
        total_dropouts = total_enrollments - completed
        dropout_rate = (total_dropouts / total_enrollments) * 100

        # 평균 이탈 지점 (난이도에 따라 다름)
        avg_dropout = {
            DifficultyLevel.BEGINNER: random.uniform(18, 35),
            DifficultyLevel.INTERMEDIATE: random.uniform(22, 40),
            DifficultyLevel.ADVANCED: random.uniform(15, 30),
        }.get(course_info.difficulty, 25)

        # 최다 이탈 구간
        peak_segments = ["0-10%", "10-20%", "20-30%"]
        peak_segment = random.choice(peak_segments)
        peak_dropout_rate = random.uniform(18, 35)

        # 참여도 지표
        avg_watch_time = course_info.duration_hours * 60 * random.uniform(0.6, 0.9)
        avg_sessions = random.uniform(8, 25)
        avg_days_to_complete = random.uniform(14, 60)
        rewatch_rate = random.uniform(5, 25)

        return {
            "enrollment": {
                "total_enrollments": total_enrollments,
                "active_learners": int(total_enrollments * random.uniform(0.15, 0.35)),
                "watched_at_least_once": watched_at_least_once,
                "watched_rate": round(watched_rate * 100, 1)
            },
            "progress": {
                "reached_25": reached_25,
                "reached_50": reached_50,
                "reached_75": reached_75,
                "completed": completed,
                "reached_25_rate": round(reached_25_rate * 100, 1),
                "reached_50_rate": round(reached_50_rate * 100, 1),
                "reached_75_rate": round(reached_75_rate * 100, 1),
                "completion_rate": round(completion_rate * 100, 1)
            },
            "dropout": {
                "total_dropouts": total_dropouts,
                "dropout_rate": round(dropout_rate, 1),
                "avg_dropout_point": round(avg_dropout, 1),
                "peak_segment": peak_segment,
                "peak_dropout_rate": round(peak_dropout_rate, 1)
            },
            "engagement": {
                "avg_watch_time": round(avg_watch_time, 1),
                "avg_sessions": round(avg_sessions, 1),
                "avg_days_to_complete": round(avg_days_to_complete, 1),
                "rewatch_rate": round(rewatch_rate, 1)
            }
        }

    def get_course_detail(self, course_id: str) -> Optional[CourseDetailAnalysis]:
        """강의 상세 분석 조회"""
        if course_id not in self.courses:
            return None

        course_info = self.courses[course_id]
        metrics = self._generated_metrics[course_id]

        # 퍼널 데이터 생성
        funnel_data = [
            {"stage": "수강신청", "count": metrics["enrollment"]["total_enrollments"], "rate": 100},
            {"stage": "1회 이상 시청", "count": metrics["enrollment"]["watched_at_least_once"],
             "rate": metrics["enrollment"]["watched_rate"]},
            {"stage": "25% 진도", "count": metrics["progress"]["reached_25"],
             "rate": metrics["progress"]["reached_25_rate"]},
            {"stage": "50% 진도", "count": metrics["progress"]["reached_50"],
             "rate": metrics["progress"]["reached_50_rate"]},
            {"stage": "75% 진도", "count": metrics["progress"]["reached_75"],
             "rate": metrics["progress"]["reached_75_rate"]},
            {"stage": "완강", "count": metrics["progress"]["completed"],
             "rate": metrics["progress"]["completion_rate"]},
        ]

        # 평균 대비 비교
        avg_completion = 28.5  # 업계 평균 완강률
        avg_dropout = 71.5
        avg_watch_time = 180

        comparison = {
            "completion_rate": {
                "value": metrics["progress"]["completion_rate"],
                "average": avg_completion,
                "diff": round(metrics["progress"]["completion_rate"] - avg_completion, 1),
                "is_above_average": metrics["progress"]["completion_rate"] > avg_completion
            },
            "dropout_rate": {
                "value": metrics["dropout"]["dropout_rate"],
                "average": avg_dropout,
                "diff": round(metrics["dropout"]["dropout_rate"] - avg_dropout, 1),
                "is_above_average": metrics["dropout"]["dropout_rate"] > avg_dropout
            },
            "engagement": {
                "value": metrics["engagement"]["avg_watch_time"],
                "average": avg_watch_time,
                "diff": round(metrics["engagement"]["avg_watch_time"] - avg_watch_time, 1),
                "is_above_average": metrics["engagement"]["avg_watch_time"] > avg_watch_time
            }
        }

        return CourseDetailAnalysis(
            course_info=course_info,
            enrollment_metrics=EnrollmentMetrics(
                total_enrollments=metrics["enrollment"]["total_enrollments"],
                active_learners=metrics["enrollment"]["active_learners"],
                watched_at_least_once=metrics["enrollment"]["watched_at_least_once"],
                watched_at_least_once_rate=metrics["enrollment"]["watched_rate"]
            ),
            progress_metrics=ProgressMetrics(
                reached_25_percent=metrics["progress"]["reached_25"],
                reached_50_percent=metrics["progress"]["reached_50"],
                reached_75_percent=metrics["progress"]["reached_75"],
                completed=metrics["progress"]["completed"],
                reached_25_rate=metrics["progress"]["reached_25_rate"],
                reached_50_rate=metrics["progress"]["reached_50_rate"],
                reached_75_rate=metrics["progress"]["reached_75_rate"],
                completion_rate=metrics["progress"]["completion_rate"]
            ),
            dropout_metrics=DropoutMetrics(
                total_dropouts=metrics["dropout"]["total_dropouts"],
                dropout_rate=metrics["dropout"]["dropout_rate"],
                average_dropout_point=metrics["dropout"]["avg_dropout_point"],
                peak_dropout_segment=metrics["dropout"]["peak_segment"],
                peak_dropout_rate=metrics["dropout"]["peak_dropout_rate"]
            ),
            engagement_metrics=EngagementMetrics(
                average_watch_time_minutes=metrics["engagement"]["avg_watch_time"],
                average_sessions_per_user=metrics["engagement"]["avg_sessions"],
                average_days_to_complete=metrics["engagement"]["avg_days_to_complete"],
                rewatch_rate=metrics["engagement"]["rewatch_rate"]
            ),
            funnel_data=funnel_data,
            comparison_with_average=comparison
        )

    def get_all_courses_summary(self) -> list[CourseSummaryCard]:
        """모든 강의 요약 목록"""
        summaries = []

        for course_id, course_info in self.courses.items():
            metrics = self._generated_metrics[course_id]

            summaries.append(CourseSummaryCard(
                course_id=course_id,
                title=course_info.title,
                category=course_info.category.value,
                difficulty=course_info.difficulty.value,
                total_enrollments=metrics["enrollment"]["total_enrollments"],
                completion_rate=metrics["progress"]["completion_rate"],
                average_rating=round(random.uniform(4.0, 4.9), 1),
                dropout_rate=metrics["dropout"]["dropout_rate"],
                is_popular=metrics["enrollment"]["total_enrollments"] > 1500,
                is_recommended=metrics["progress"]["completion_rate"] > 30
            ))

        # 수강신청자 수 기준 정렬
        return sorted(summaries, key=lambda x: x.total_enrollments, reverse=True)

    def get_courses_by_category(self, category: CourseCategory) -> list[CourseSummaryCard]:
        """카테고리별 강의 목록"""
        all_courses = self.get_all_courses_summary()
        return [c for c in all_courses if c.category == category.value]

    def get_courses_by_difficulty(self, difficulty: DifficultyLevel) -> list[CourseSummaryCard]:
        """난이도별 강의 목록"""
        all_courses = self.get_all_courses_summary()
        return [c for c in all_courses if c.difficulty == difficulty.value]

    def get_top_completion_courses(self, limit: int = 5) -> list[CourseSummaryCard]:
        """완강률 높은 강의 TOP N"""
        all_courses = self.get_all_courses_summary()
        return sorted(all_courses, key=lambda x: x.completion_rate, reverse=True)[:limit]

    def get_funnel_comparison(self, course_ids: list[str]) -> dict:
        """여러 강의 퍼널 비교"""
        comparison = {}

        for course_id in course_ids:
            if course_id in self._generated_metrics:
                metrics = self._generated_metrics[course_id]
                comparison[course_id] = {
                    "title": self.courses[course_id].title,
                    "funnel": {
                        "enrolled": 100,
                        "watched": metrics["enrollment"]["watched_rate"],
                        "25%": metrics["progress"]["reached_25_rate"],
                        "50%": metrics["progress"]["reached_50_rate"],
                        "75%": metrics["progress"]["reached_75_rate"],
                        "completed": metrics["progress"]["completion_rate"]
                    }
                }

        return comparison


# 테스트
if __name__ == "__main__":
    analyzer = CourseAnalyzer(seed=42)

    # 전체 강의 목록
    print("=== 전체 강의 목록 ===")
    for course in analyzer.get_all_courses_summary():
        print(f"{course.title}: 수강 {course.total_enrollments}명, 완강률 {course.completion_rate}%")

    # 상세 분석
    print("\n=== Python 기초 완성 상세 분석 ===")
    detail = analyzer.get_course_detail("course_001")
    if detail:
        print(f"수강신청: {detail.enrollment_metrics.total_enrollments}명")
        print(f"1회 이상 시청: {detail.enrollment_metrics.watched_at_least_once}명 ({detail.enrollment_metrics.watched_at_least_once_rate}%)")
        print(f"50% 이상 진도: {detail.progress_metrics.reached_50_percent}명 ({detail.progress_metrics.reached_50_rate}%)")
        print(f"완강: {detail.progress_metrics.completed}명 ({detail.progress_metrics.completion_rate}%)")
        print(f"평균 이탈 지점: {detail.dropout_metrics.average_dropout_point}%")
