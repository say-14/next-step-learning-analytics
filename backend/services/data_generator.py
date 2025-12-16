"""
랜덤 학습 로그 데이터 생성기
실제 학습 패턴을 모방하여 현실적인 이탈 데이터 생성
"""
import random
from datetime import datetime, timedelta
from typing import Optional
import numpy as np


class LearningDataGenerator:
    """학습 로그 데이터 랜덤 생성기"""

    # 실제 학습 패턴을 반영한 이탈 확률 (구간별)
    # 연구에 따르면 초반과 중반에 이탈이 많음
    DROPOUT_PROBABILITY = {
        (0, 10): 0.25,    # 첫 10% - 콘텐츠가 기대와 다름
        (10, 20): 0.15,   # 10-20% - 난이도 체감
        (20, 30): 0.12,   # 20-30% - 지루함 시작
        (30, 40): 0.10,   # 30-40% - 중간 슬럼프
        (40, 50): 0.08,   # 40-50% - 절반 고비
        (50, 60): 0.06,   # 50-60% - 후반 진입
        (60, 70): 0.05,   # 60-70% - 완주 의지
        (70, 80): 0.04,   # 70-80% - 거의 다 옴
        (80, 90): 0.03,   # 80-90% - 마지막 스퍼트
        (90, 100): 0.02,  # 90-100% - 완주 직전
    }

    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)

    def generate_single_user_log(
        self,
        user_id: str,
        course_id: str,
        course_duration_min: int = 300,  # 강의 총 길이 (분)
        start_date: Optional[datetime] = None
    ) -> list[dict]:
        """
        단일 사용자의 학습 로그 생성

        Returns:
            list[dict]: 학습 로그 리스트
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=random.randint(1, 30))

        logs = []
        current_progress = 0.0
        current_time = start_date

        while current_progress < 100:
            # 현재 구간의 이탈 확률 확인
            dropout_prob = self._get_dropout_probability(current_progress)

            # 이탈 여부 결정
            if random.random() < dropout_prob:
                # 이탈 로그 기록
                logs.append({
                    "user_id": user_id,
                    "course_id": course_id,
                    "timestamp": current_time.isoformat(),
                    "progress_percent": round(current_progress, 1),
                    "watch_duration_sec": random.randint(60, 600),
                    "is_dropout": True,
                    "dropout_reason": self._get_dropout_reason(current_progress)
                })
                break

            # 정상 학습 진행
            progress_increment = random.uniform(2, 8)  # 2~8% 씩 진행
            watch_duration = int((progress_increment / 100) * course_duration_min * 60)

            logs.append({
                "user_id": user_id,
                "course_id": course_id,
                "timestamp": current_time.isoformat(),
                "progress_percent": round(min(current_progress + progress_increment, 100), 1),
                "watch_duration_sec": watch_duration,
                "is_dropout": False
            })

            current_progress += progress_increment
            # 다음 학습까지 시간 간격 (1시간 ~ 3일)
            current_time += timedelta(hours=random.randint(1, 72))

        # 완주한 경우
        if current_progress >= 100:
            logs[-1]["progress_percent"] = 100.0
            logs[-1]["is_completed"] = True

        return logs

    def generate_course_logs(
        self,
        course_id: str,
        num_users: int = 100,
        course_duration_min: int = 300
    ) -> list[dict]:
        """
        강의에 대한 여러 사용자의 학습 로그 생성
        """
        all_logs = []

        for i in range(num_users):
            user_id = f"user_{i+1:04d}"
            user_logs = self.generate_single_user_log(
                user_id=user_id,
                course_id=course_id,
                course_duration_min=course_duration_min
            )
            all_logs.extend(user_logs)

        return all_logs

    def _get_dropout_probability(self, progress: float) -> float:
        """진도율에 따른 이탈 확률 반환"""
        for (start, end), prob in self.DROPOUT_PROBABILITY.items():
            if start <= progress < end:
                return prob
        return 0.02  # 기본값

    def _get_dropout_reason(self, progress: float) -> str:
        """진도율에 따른 예상 이탈 사유"""
        if progress < 10:
            reasons = ["기대와 다른 내용", "난이도 불일치", "강의 스타일 불만"]
        elif progress < 30:
            reasons = ["시간 부족", "내용이 어려움", "집중력 저하"]
        elif progress < 50:
            reasons = ["중간 슬럼프", "다른 강의로 이동", "실습 환경 문제"]
        elif progress < 70:
            reasons = ["번아웃", "목표 달성 (부분)", "외부 요인"]
        else:
            reasons = ["거의 완료로 만족", "시험/프로젝트 우선", "기타"]

        return random.choice(reasons)

    def generate_multiple_courses(
        self,
        num_courses: int = 5,
        users_per_course: int = 100
    ) -> dict[str, list[dict]]:
        """여러 강의에 대한 학습 로그 생성"""
        course_names = [
            "Python 기초 완성",
            "FastAPI 마스터",
            "Django 웹 개발",
            "데이터 분석 입문",
            "머신러닝 기초",
            "React 프론트엔드",
            "SQL 데이터베이스",
            "Docker 컨테이너",
            "AWS 클라우드",
            "알고리즘 문제풀이"
        ]

        all_course_logs = {}

        for i in range(min(num_courses, len(course_names))):
            course_id = f"course_{i+1:03d}"
            logs = self.generate_course_logs(
                course_id=course_id,
                num_users=users_per_course
            )
            all_course_logs[course_id] = {
                "course_title": course_names[i],
                "logs": logs
            }

        return all_course_logs


# 테스트용 실행
if __name__ == "__main__":
    generator = LearningDataGenerator(seed=42)

    # 단일 강의 로그 생성
    logs = generator.generate_course_logs("course_001", num_users=50)

    print(f"생성된 로그 수: {len(logs)}")
    print(f"\n샘플 로그:")
    for log in logs[:5]:
        print(log)
