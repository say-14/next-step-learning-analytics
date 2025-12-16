"""
사용자 레벨 자동 추정 서비스
Rule-based + ML (Logistic Regression / Random Forest) 지원
"""
from typing import Optional
import numpy as np

from models.user_schemas import (
    UserLevelRequest, UserLevelResponse, UserLevel,
    JobRole, EducationLevel, BasicConcept
)


class UserLevelEstimator:
    """사용자 레벨 추정기"""

    # 학력별 기본 점수
    EDUCATION_SCORES = {
        EducationLevel.HIGH_SCHOOL: 1,
        EducationLevel.COLLEGE: 2,
        EducationLevel.UNIVERSITY_NON_CS: 3,
        EducationLevel.UNIVERSITY_CS: 5,
        EducationLevel.GRADUATE: 6,
        EducationLevel.BOOTCAMP: 4,
    }

    # 개념별 가중치
    CONCEPT_WEIGHTS = {
        BasicConcept.VARIABLE: 1,
        BasicConcept.LOOP: 1,
        BasicConcept.FUNCTION: 1.5,
        BasicConcept.HTTP: 2,
        BasicConcept.DATABASE: 2,
        BasicConcept.GIT: 1.5,
        BasicConcept.ALGORITHM: 2.5,
        BasicConcept.OOP: 2.5,
    }

    # 직무별 중요 개념
    ROLE_IMPORTANT_CONCEPTS = {
        JobRole.BACKEND: [BasicConcept.HTTP, BasicConcept.DATABASE, BasicConcept.OOP],
        JobRole.FRONTEND: [BasicConcept.VARIABLE, BasicConcept.FUNCTION, BasicConcept.HTTP],
        JobRole.DATA: [BasicConcept.VARIABLE, BasicConcept.LOOP, BasicConcept.DATABASE],
        JobRole.AI: [BasicConcept.ALGORITHM, BasicConcept.OOP, BasicConcept.FUNCTION],
        JobRole.FULLSTACK: [BasicConcept.HTTP, BasicConcept.DATABASE, BasicConcept.GIT],
        JobRole.DEVOPS: [BasicConcept.GIT, BasicConcept.HTTP, BasicConcept.DATABASE],
    }

    # 레벨별 설명
    LEVEL_DESCRIPTIONS = {
        UserLevel.ABSOLUTE_BEGINNER: "코딩을 처음 시작하는 단계입니다. 기초부터 차근차근 배워나가세요!",
        UserLevel.BEGINNER: "기초 개념은 알고 있지만 실전 경험이 부족한 단계입니다.",
        UserLevel.JUNIOR_READY: "신입 개발자로 취업을 준비할 수 있는 수준입니다.",
        UserLevel.DATA_FOCUSED: "데이터 분석/사이언스 분야에 적합한 역량을 갖추고 있습니다.",
        UserLevel.WEB_FOCUSED: "웹 개발 분야에 적합한 역량을 갖추고 있습니다.",
        UserLevel.AI_FOCUSED: "AI/ML 분야에 적합한 역량을 갖추고 있습니다.",
        UserLevel.INTERMEDIATE: "중급 수준의 개발 역량을 보유하고 있습니다.",
    }

    def __init__(self, use_ml: bool = False):
        """
        Args:
            use_ml: True면 ML 모델 사용, False면 규칙 기반
        """
        self.use_ml = use_ml
        self.ml_model = None

        if use_ml:
            self._initialize_ml_model()

    def _initialize_ml_model(self):
        """ML 모델 초기화 (간단한 학습 데이터로 훈련)"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import LabelEncoder

            # 샘플 학습 데이터 생성 (실제로는 DB에서 가져옴)
            X, y = self._generate_training_data()

            self.label_encoder = LabelEncoder()
            y_encoded = self.label_encoder.fit_transform(y)

            self.ml_model = RandomForestClassifier(
                n_estimators=50,
                max_depth=5,
                random_state=42
            )
            self.ml_model.fit(X, y_encoded)

        except ImportError:
            print("sklearn이 설치되지 않았습니다. 규칙 기반으로 전환합니다.")
            self.use_ml = False

    def _generate_training_data(self) -> tuple:
        """학습용 샘플 데이터 생성"""
        # 특성: [education_score, study_hours, concept_count, concept_score,
        #        has_project, coding_months, role_match_score]
        X = []
        y = []

        # Absolute Beginner 샘플
        for _ in range(50):
            X.append([1, np.random.uniform(0.5, 2), 0, 0, 0, 0, 0])
            y.append(UserLevel.ABSOLUTE_BEGINNER.value)

        # Beginner 샘플
        for _ in range(50):
            X.append([2, np.random.uniform(1, 3), np.random.randint(1, 4),
                     np.random.uniform(1, 5), 0, np.random.randint(0, 3),
                     np.random.uniform(0, 3)])
            y.append(UserLevel.BEGINNER.value)

        # Junior Ready 샘플
        for _ in range(50):
            X.append([4, np.random.uniform(2, 5), np.random.randint(4, 8),
                     np.random.uniform(5, 12), 1, np.random.randint(6, 18),
                     np.random.uniform(3, 8)])
            y.append(UserLevel.JUNIOR_READY.value)

        # Data Focused 샘플
        for _ in range(30):
            X.append([4, np.random.uniform(2, 4), np.random.randint(3, 6),
                     np.random.uniform(4, 10), np.random.randint(0, 2),
                     np.random.randint(3, 12), np.random.uniform(4, 8)])
            y.append(UserLevel.DATA_FOCUSED.value)

        # Web Focused 샘플
        for _ in range(30):
            X.append([3, np.random.uniform(2, 4), np.random.randint(3, 6),
                     np.random.uniform(4, 10), np.random.randint(0, 2),
                     np.random.randint(3, 12), np.random.uniform(4, 8)])
            y.append(UserLevel.WEB_FOCUSED.value)

        return np.array(X), y

    def estimate_level(self, request: UserLevelRequest) -> UserLevelResponse:
        """
        사용자 레벨 추정

        Args:
            request: 사용자 정보

        Returns:
            UserLevelResponse: 추정 결과
        """
        # 세부 점수 계산
        detail_scores = self._calculate_detail_scores(request)

        if self.use_ml and self.ml_model is not None:
            level, confidence = self._predict_with_ml(detail_scores)
        else:
            level, confidence = self._predict_with_rules(request, detail_scores)

        # 추천 학습 경로 생성
        recommended_path = self._generate_learning_path(level, request.desired_role)

        # 강점/약점 분석
        strengths = self._analyze_strengths(request, detail_scores)
        areas_to_improve = self._analyze_weaknesses(request, detail_scores)

        # 취업 준비 예상 기간
        time_estimate = self._estimate_time_to_ready(level, request)

        return UserLevelResponse(
            estimated_level=level,
            level_description=self.LEVEL_DESCRIPTIONS[level],
            confidence_score=round(confidence, 2),
            recommended_path=recommended_path,
            strengths=strengths,
            areas_to_improve=areas_to_improve,
            estimated_time_to_job_ready=time_estimate,
            detail_scores=detail_scores
        )

    def _calculate_detail_scores(self, request: UserLevelRequest) -> dict:
        """세부 점수 계산"""
        # 학력 점수
        education_score = self.EDUCATION_SCORES.get(request.education, 2)

        # 개념 점수
        concept_score = sum(
            self.CONCEPT_WEIGHTS.get(concept, 1)
            for concept in request.known_concepts
        )
        max_concept_score = sum(self.CONCEPT_WEIGHTS.values())
        concept_percentage = (concept_score / max_concept_score * 100) if max_concept_score > 0 else 0

        # 직무 매칭 점수
        important_concepts = self.ROLE_IMPORTANT_CONCEPTS.get(request.desired_role, [])
        matched_concepts = [c for c in request.known_concepts if c in important_concepts]
        role_match_score = len(matched_concepts) / len(important_concepts) * 10 if important_concepts else 0

        # 경험 점수
        experience_score = min(request.coding_months / 12 * 5, 10)  # 최대 10점
        if request.has_project_experience:
            experience_score += 3

        # 학습 의지 점수 (공부 시간 기반)
        commitment_score = min(request.daily_study_hours / 4 * 10, 10)

        # 총점 계산 (100점 만점)
        total_score = (
            education_score * 3 +      # 최대 18점
            concept_percentage * 0.3 + # 최대 30점
            role_match_score * 2 +     # 최대 20점
            experience_score * 2 +     # 최대 26점
            commitment_score * 0.6     # 최대 6점
        )

        return {
            "education_score": education_score,
            "concept_count": len(request.known_concepts),
            "concept_score": round(concept_score, 1),
            "concept_percentage": round(concept_percentage, 1),
            "role_match_score": round(role_match_score, 1),
            "experience_score": round(experience_score, 1),
            "commitment_score": round(commitment_score, 1),
            "total_score": round(total_score, 1)
        }

    def _predict_with_rules(self, request: UserLevelRequest, scores: dict) -> tuple:
        """규칙 기반 레벨 예측"""
        total = scores["total_score"]
        concept_count = scores["concept_count"]
        role = request.desired_role

        # 완전 초보
        if concept_count == 0 and request.coding_months == 0:
            return UserLevel.ABSOLUTE_BEGINNER, 0.95

        # 초보
        if total < 30 or concept_count < 3:
            return UserLevel.BEGINNER, 0.85

        # 직무 특화 판단
        if 30 <= total < 60:
            if role in [JobRole.DATA, JobRole.AI] and scores["role_match_score"] >= 5:
                if role == JobRole.DATA:
                    return UserLevel.DATA_FOCUSED, 0.75
                else:
                    return UserLevel.AI_FOCUSED, 0.75
            elif role in [JobRole.FRONTEND, JobRole.BACKEND, JobRole.FULLSTACK]:
                if scores["role_match_score"] >= 5:
                    return UserLevel.WEB_FOCUSED, 0.75

            return UserLevel.BEGINNER, 0.70

        # Junior Ready
        if 60 <= total < 80:
            if request.has_project_experience and request.coding_months >= 6:
                return UserLevel.JUNIOR_READY, 0.80

            # 직무 특화로 분류
            if role in [JobRole.DATA]:
                return UserLevel.DATA_FOCUSED, 0.75
            elif role in [JobRole.AI]:
                return UserLevel.AI_FOCUSED, 0.75
            elif role in [JobRole.FRONTEND, JobRole.BACKEND, JobRole.FULLSTACK]:
                return UserLevel.WEB_FOCUSED, 0.75

        # 중급 이상
        if total >= 80:
            if request.has_project_experience:
                return UserLevel.INTERMEDIATE, 0.85
            return UserLevel.JUNIOR_READY, 0.80

        return UserLevel.BEGINNER, 0.60

    def _predict_with_ml(self, scores: dict) -> tuple:
        """ML 모델로 레벨 예측"""
        features = np.array([[
            scores["education_score"],
            scores["commitment_score"],
            scores["concept_count"],
            scores["concept_score"],
            1 if scores["experience_score"] > 3 else 0,  # has_project 대용
            int(scores["experience_score"] * 2),  # coding_months 대용
            scores["role_match_score"]
        ]])

        prediction = self.ml_model.predict(features)[0]
        probabilities = self.ml_model.predict_proba(features)[0]
        confidence = float(max(probabilities))

        level_value = self.label_encoder.inverse_transform([prediction])[0]
        return UserLevel(level_value), confidence

    def _generate_learning_path(self, level: UserLevel, role: JobRole) -> list[str]:
        """레벨과 희망 직무에 따른 학습 경로 생성"""
        paths = {
            (UserLevel.ABSOLUTE_BEGINNER, JobRole.BACKEND): [
                "Python 기초 문법",
                "자료구조 기초",
                "HTTP와 웹 기초",
                "FastAPI/Django 입문",
                "데이터베이스 SQL 기초",
                "REST API 설계",
                "포트폴리오 프로젝트"
            ],
            (UserLevel.ABSOLUTE_BEGINNER, JobRole.FRONTEND): [
                "HTML/CSS 기초",
                "JavaScript 기초",
                "DOM 조작과 이벤트",
                "React/Vue 입문",
                "상태관리 기초",
                "API 연동",
                "포트폴리오 프로젝트"
            ],
            (UserLevel.ABSOLUTE_BEGINNER, JobRole.DATA): [
                "Python 기초",
                "데이터 타입과 자료구조",
                "Pandas 기초",
                "데이터 시각화 (Matplotlib)",
                "SQL 기초",
                "데이터 분석 프로젝트",
                "통계 기초"
            ],
            (UserLevel.ABSOLUTE_BEGINNER, JobRole.AI): [
                "Python 기초",
                "수학 기초 (선형대수, 통계)",
                "NumPy/Pandas",
                "Scikit-learn 입문",
                "머신러닝 기초 이론",
                "딥러닝 기초",
                "AI 프로젝트"
            ],
            (UserLevel.BEGINNER, JobRole.BACKEND): [
                "Python 심화",
                "REST API 설계",
                "데이터베이스 심화",
                "인증/인가 구현",
                "테스트 코드 작성",
                "배포 기초 (Docker)"
            ],
            (UserLevel.BEGINNER, JobRole.DATA): [
                "Pandas 심화",
                "데이터 전처리 기법",
                "통계 분석",
                "시각화 심화",
                "SQL 심화",
                "분석 프로젝트"
            ],
            (UserLevel.JUNIOR_READY, JobRole.BACKEND): [
                "시스템 설계 기초",
                "성능 최적화",
                "CI/CD 파이프라인",
                "모니터링/로깅",
                "면접 준비"
            ],
            (UserLevel.DATA_FOCUSED, JobRole.DATA): [
                "고급 분석 기법",
                "ML 기초",
                "A/B 테스트",
                "대시보드 구축",
                "포트폴리오 정리"
            ],
        }

        # 기본 경로
        default_paths = {
            UserLevel.ABSOLUTE_BEGINNER: ["프로그래밍 기초", "자료구조", "직무 기초 강의", "실습 프로젝트"],
            UserLevel.BEGINNER: ["직무 심화", "실전 프로젝트", "협업 도구 (Git)", "코드 리뷰 경험"],
            UserLevel.JUNIOR_READY: ["면접 준비", "알고리즘 문제풀이", "포트폴리오 정리", "기술 블로그 작성"],
            UserLevel.DATA_FOCUSED: ["ML/통계 심화", "분석 프로젝트", "포트폴리오 정리"],
            UserLevel.WEB_FOCUSED: ["프레임워크 심화", "배포/운영", "포트폴리오 정리"],
            UserLevel.AI_FOCUSED: ["딥러닝 심화", "논문 구현", "Kaggle 도전"],
            UserLevel.INTERMEDIATE: ["시스템 설계", "오픈소스 기여", "기술 리더십"],
        }

        return paths.get((level, role), default_paths.get(level, []))

    def _analyze_strengths(self, request: UserLevelRequest, scores: dict) -> list[str]:
        """강점 분석"""
        strengths = []

        if scores["education_score"] >= 4:
            strengths.append("CS 관련 학력/전공 보유")

        if scores["commitment_score"] >= 7:
            strengths.append("충분한 학습 시간 확보 가능")

        if scores["concept_count"] >= 5:
            strengths.append("다양한 기초 개념 이해")

        if request.has_project_experience:
            strengths.append("실전 프로젝트 경험 보유")

        if request.coding_months >= 6:
            strengths.append("지속적인 코딩 경험")

        if scores["role_match_score"] >= 7:
            strengths.append(f"{request.desired_role.value} 직무에 필요한 개념 이해도 높음")

        return strengths if strengths else ["학습 의지가 중요합니다!"]

    def _analyze_weaknesses(self, request: UserLevelRequest, scores: dict) -> list[str]:
        """약점/개선점 분석"""
        weaknesses = []

        if scores["concept_count"] < 3:
            weaknesses.append("기초 개념 학습 필요")

        important_concepts = self.ROLE_IMPORTANT_CONCEPTS.get(request.desired_role, [])
        missing_concepts = [c for c in important_concepts if c not in request.known_concepts]
        if missing_concepts:
            concept_names = {
                BasicConcept.VARIABLE: "변수",
                BasicConcept.LOOP: "반복문",
                BasicConcept.FUNCTION: "함수",
                BasicConcept.HTTP: "HTTP",
                BasicConcept.DATABASE: "데이터베이스",
                BasicConcept.GIT: "Git",
                BasicConcept.ALGORITHM: "알고리즘",
                BasicConcept.OOP: "객체지향",
            }
            missing_names = [concept_names.get(c, c.value) for c in missing_concepts]
            weaknesses.append(f"직무 핵심 개념 학습 필요: {', '.join(missing_names)}")

        if not request.has_project_experience:
            weaknesses.append("프로젝트 경험 쌓기 필요")

        if scores["commitment_score"] < 4:
            weaknesses.append("학습 시간 확보 필요")

        return weaknesses if weaknesses else ["현재 수준에서 꾸준히 성장하세요!"]

    def _estimate_time_to_ready(self, level: UserLevel, request: UserLevelRequest) -> str:
        """취업 준비 예상 기간"""
        base_months = {
            UserLevel.ABSOLUTE_BEGINNER: 12,
            UserLevel.BEGINNER: 8,
            UserLevel.JUNIOR_READY: 2,
            UserLevel.DATA_FOCUSED: 4,
            UserLevel.WEB_FOCUSED: 4,
            UserLevel.AI_FOCUSED: 6,
            UserLevel.INTERMEDIATE: 1,
        }

        months = base_months.get(level, 6)

        # 학습 시간에 따른 조정
        if request.daily_study_hours >= 6:
            months = int(months * 0.7)
        elif request.daily_study_hours >= 4:
            months = int(months * 0.85)
        elif request.daily_study_hours < 2:
            months = int(months * 1.5)

        if months < 1:
            return "1개월 이내"
        elif months == 1:
            return "약 1개월"
        elif months <= 3:
            return f"약 {months}개월"
        elif months <= 6:
            return f"약 {months}개월 (3~6개월)"
        elif months <= 12:
            return f"약 {months}개월 (6개월~1년)"
        else:
            return "1년 이상"


# 테스트
if __name__ == "__main__":
    estimator = UserLevelEstimator(use_ml=False)

    # 테스트 케이스 1: 완전 초보
    request1 = UserLevelRequest(
        education=EducationLevel.HIGH_SCHOOL,
        daily_study_hours=2,
        known_concepts=[],
        desired_role=JobRole.BACKEND,
        has_project_experience=False,
        coding_months=0
    )
    result1 = estimator.estimate_level(request1)
    print(f"Test 1: {result1.estimated_level.value} (confidence: {result1.confidence_score})")

    # 테스트 케이스 2: 중급
    request2 = UserLevelRequest(
        education=EducationLevel.UNIVERSITY_CS,
        daily_study_hours=4,
        known_concepts=[
            BasicConcept.VARIABLE, BasicConcept.LOOP, BasicConcept.FUNCTION,
            BasicConcept.HTTP, BasicConcept.DATABASE, BasicConcept.GIT, BasicConcept.OOP
        ],
        desired_role=JobRole.BACKEND,
        has_project_experience=True,
        coding_months=12
    )
    result2 = estimator.estimate_level(request2)
    print(f"Test 2: {result2.estimated_level.value} (confidence: {result2.confidence_score})")
