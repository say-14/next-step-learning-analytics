"""
개인화 추천 알고리즘 서비스
규칙 기반 + 협업 필터링 (Cosine Similarity)
"""
import random
from typing import Optional
from collections import defaultdict
import numpy as np

from models.user_schemas import (
    UserProfile, UserLevel, JobRole, BasicConcept
)
from models.course_schemas import (
    CourseCategory, DifficultyLevel, CourseSummaryCard
)
from services.course_analyzer import CourseAnalyzer


class CourseRecommender:
    """강의 추천 시스템"""

    # 직무별 관련 카테고리 매핑
    ROLE_CATEGORIES = {
        JobRole.BACKEND: [
            CourseCategory.PYTHON, CourseCategory.JAVA,
            CourseCategory.WEB_BACKEND, CourseCategory.DATABASE
        ],
        JobRole.FRONTEND: [
            CourseCategory.JAVASCRIPT, CourseCategory.WEB_FRONTEND
        ],
        JobRole.DATA: [
            CourseCategory.PYTHON, CourseCategory.DATA_ANALYSIS,
            CourseCategory.DATABASE
        ],
        JobRole.AI: [
            CourseCategory.PYTHON, CourseCategory.MACHINE_LEARNING,
            CourseCategory.DATA_ANALYSIS
        ],
        JobRole.FULLSTACK: [
            CourseCategory.PYTHON, CourseCategory.JAVASCRIPT,
            CourseCategory.WEB_BACKEND, CourseCategory.WEB_FRONTEND,
            CourseCategory.DATABASE
        ],
        JobRole.DEVOPS: [
            CourseCategory.DEVOPS, CourseCategory.DATABASE,
            CourseCategory.PYTHON
        ],
    }

    # 레벨별 권장 난이도
    LEVEL_DIFFICULTY = {
        UserLevel.ABSOLUTE_BEGINNER: [DifficultyLevel.BEGINNER],
        UserLevel.BEGINNER: [DifficultyLevel.BEGINNER],
        UserLevel.JUNIOR_READY: [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED],
        UserLevel.DATA_FOCUSED: [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE],
        UserLevel.WEB_FOCUSED: [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE],
        UserLevel.AI_FOCUSED: [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED],
        UserLevel.INTERMEDIATE: [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED],
    }

    def __init__(self, course_analyzer: Optional[CourseAnalyzer] = None, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)

        self.course_analyzer = course_analyzer or CourseAnalyzer(seed=seed)
        self._user_course_matrix = None
        self._similarity_matrix = None
        self._user_ids = []
        self._course_ids = []

        # 협업 필터링용 가상 사용자 데이터 생성
        self._generate_user_data()

    def _generate_user_data(self):
        """협업 필터링을 위한 가상 사용자-강의 행렬 생성"""
        courses = self.course_analyzer.get_all_courses_summary()
        self._course_ids = [c.course_id for c in courses]

        # 가상 사용자 100명 생성
        num_users = 100
        self._user_ids = [f"user_{i:04d}" for i in range(num_users)]

        # 사용자-강의 평점 행렬 (0: 수강 안함, 1-5: 평점)
        self._user_course_matrix = np.zeros((num_users, len(self._course_ids)))

        # 각 사용자별로 랜덤하게 수강 및 평점 부여
        for i in range(num_users):
            # 각 사용자는 2~6개 강의 수강
            num_courses = random.randint(2, 6)
            selected_courses = random.sample(range(len(self._course_ids)), num_courses)

            for course_idx in selected_courses:
                # 완강률이 높은 강의에 더 높은 평점 부여 경향
                course = courses[course_idx]
                base_rating = 3 + (course.completion_rate / 100) * 2  # 완강률 반영
                rating = min(5, max(1, base_rating + random.uniform(-1, 1)))
                self._user_course_matrix[i, course_idx] = round(rating, 1)

        # 코사인 유사도 행렬 계산
        self._calculate_similarity_matrix()

    def _calculate_similarity_matrix(self):
        """사용자 간 코사인 유사도 계산"""
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            # 강의 기반 유사도 (아이템-아이템 협업 필터링)
            self._similarity_matrix = cosine_similarity(self._user_course_matrix.T)
        except ImportError:
            # sklearn 없으면 직접 계산
            matrix = self._user_course_matrix.T
            norm = np.linalg.norm(matrix, axis=1, keepdims=True)
            norm[norm == 0] = 1  # 0으로 나누기 방지
            normalized = matrix / norm
            self._similarity_matrix = np.dot(normalized, normalized.T)

    def recommend_rule_based(
        self,
        user_profile: UserProfile,
        limit: int = 5
    ) -> list[dict]:
        """
        규칙 기반 추천

        - 초보자: 초급 난이도 + 완주율 높은 강의 우선
        - 직무 매칭: 희망 직무와 관련된 카테고리 강의
        - 이미 수강한 강의 제외
        """
        all_courses = self.course_analyzer.get_all_courses_summary()

        # 이미 수강한 강의 제외
        excluded = set(user_profile.completed_courses + user_profile.in_progress_courses)
        available_courses = [c for c in all_courses if c.course_id not in excluded]

        scored_courses = []

        # 권장 난이도
        recommended_difficulties = self.LEVEL_DIFFICULTY.get(
            user_profile.level,
            [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE]
        )

        # 관련 카테고리
        related_categories = self.ROLE_CATEGORIES.get(
            user_profile.desired_role,
            [CourseCategory.PYTHON]
        )

        for course in available_courses:
            score = 0
            reasons = []

            # 1. 난이도 매칭 (30점)
            if course.difficulty in [d.value for d in recommended_difficulties]:
                score += 30
                reasons.append(f"레벨에 맞는 난이도 ({course.difficulty})")

            # 2. 카테고리 매칭 (30점)
            if course.category in [c.value for c in related_categories]:
                score += 30
                reasons.append(f"{user_profile.desired_role.value} 직무 관련 강의")

            # 3. 완강률 보너스 (최대 20점)
            completion_bonus = course.completion_rate * 0.5  # 완강률 40% = 20점
            score += min(20, completion_bonus)
            if course.completion_rate > 30:
                reasons.append(f"높은 완강률 ({course.completion_rate}%)")

            # 4. 인기도 보너스 (최대 10점)
            if course.is_popular:
                score += 10
                reasons.append("인기 강의")

            # 5. 낮은 이탈률 보너스 (최대 10점)
            dropout_bonus = (100 - course.dropout_rate) * 0.1
            score += min(10, dropout_bonus)

            scored_courses.append({
                "course": course,
                "score": round(score, 1),
                "reasons": reasons
            })

        # 점수 기준 정렬
        scored_courses.sort(key=lambda x: x["score"], reverse=True)

        # 상위 N개 반환
        recommendations = []
        for item in scored_courses[:limit]:
            course = item["course"]
            recommendations.append({
                "course_id": course.course_id,
                "title": course.title,
                "category": course.category,
                "difficulty": course.difficulty,
                "completion_rate": course.completion_rate,
                "total_enrollments": course.total_enrollments,
                "recommendation_score": item["score"],
                "reasons": item["reasons"],
                "method": "rule_based"
            })

        return recommendations

    def recommend_collaborative(
        self,
        user_id: str,
        completed_courses: list[str],
        limit: int = 5
    ) -> list[dict]:
        """
        협업 필터링 기반 추천 (아이템-아이템)

        사용자가 수강한 강의와 유사한 강의 추천
        """
        if not completed_courses:
            return []

        all_courses = self.course_analyzer.get_all_courses_summary()
        course_map = {c.course_id: c for c in all_courses}

        # 수강한 강의의 인덱스 찾기
        completed_indices = []
        for course_id in completed_courses:
            if course_id in self._course_ids:
                completed_indices.append(self._course_ids.index(course_id))

        if not completed_indices:
            return []

        # 각 미수강 강의에 대해 유사도 점수 계산
        scores = {}

        for i, course_id in enumerate(self._course_ids):
            if course_id in completed_courses:
                continue  # 이미 수강한 강의 제외

            # 수강한 강의들과의 평균 유사도
            similarities = [self._similarity_matrix[i, j] for j in completed_indices]
            avg_similarity = np.mean(similarities) if similarities else 0

            scores[course_id] = avg_similarity

        # 유사도 높은 순 정렬
        sorted_courses = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        recommendations = []
        for course_id, similarity in sorted_courses[:limit]:
            if course_id not in course_map:
                continue

            course = course_map[course_id]
            recommendations.append({
                "course_id": course_id,
                "title": course.title,
                "category": course.category,
                "difficulty": course.difficulty,
                "completion_rate": course.completion_rate,
                "total_enrollments": course.total_enrollments,
                "similarity_score": round(similarity, 3),
                "reason": "비슷한 강의를 수강한 사용자들이 많이 들은 강의",
                "method": "collaborative_filtering"
            })

        return recommendations

    def recommend_hybrid(
        self,
        user_profile: UserProfile,
        limit: int = 5,
        rule_weight: float = 0.6
    ) -> list[dict]:
        """
        하이브리드 추천 (규칙 기반 + 협업 필터링)

        Args:
            user_profile: 사용자 프로필
            limit: 추천 개수
            rule_weight: 규칙 기반 가중치 (0-1)
        """
        # 규칙 기반 추천
        rule_recommendations = self.recommend_rule_based(user_profile, limit=limit * 2)

        # 협업 필터링 추천 (수강 이력이 있는 경우만)
        collab_recommendations = []
        if user_profile.completed_courses:
            collab_recommendations = self.recommend_collaborative(
                user_profile.user_id,
                user_profile.completed_courses,
                limit=limit * 2
            )

        # 점수 통합
        combined_scores = {}

        for rec in rule_recommendations:
            course_id = rec["course_id"]
            combined_scores[course_id] = {
                "course": rec,
                "rule_score": rec["recommendation_score"] / 100,  # 0-1로 정규화
                "collab_score": 0
            }

        for rec in collab_recommendations:
            course_id = rec["course_id"]
            if course_id in combined_scores:
                combined_scores[course_id]["collab_score"] = rec["similarity_score"]
            else:
                combined_scores[course_id] = {
                    "course": rec,
                    "rule_score": 0,
                    "collab_score": rec["similarity_score"]
                }

        # 가중 평균 점수 계산
        final_scores = []
        collab_weight = 1 - rule_weight

        for course_id, data in combined_scores.items():
            final_score = (
                data["rule_score"] * rule_weight +
                data["collab_score"] * collab_weight
            )

            course_data = data["course"].copy()
            course_data["final_score"] = round(final_score, 3)
            course_data["method"] = "hybrid"

            # 추천 이유 통합
            reasons = []
            if data["rule_score"] > 0.5:
                reasons.append("프로필 기반 추천")
            if data["collab_score"] > 0.3:
                reasons.append("유사 사용자 추천")
            course_data["reasons"] = reasons if reasons else ["추천"]

            final_scores.append(course_data)

        # 최종 점수 기준 정렬
        final_scores.sort(key=lambda x: x["final_score"], reverse=True)

        return final_scores[:limit]

    def get_personalized_path(
        self,
        user_profile: UserProfile
    ) -> list[dict]:
        """
        맞춤형 학습 경로 추천

        레벨과 직무에 따른 단계별 강의 추천
        """
        all_courses = self.course_analyzer.get_all_courses_summary()
        related_categories = self.ROLE_CATEGORIES.get(user_profile.desired_role, [])

        # 관련 강의만 필터링
        related_courses = [
            c for c in all_courses
            if c.category in [cat.value for cat in related_categories]
        ]

        # 난이도별 분류
        by_difficulty = defaultdict(list)
        for course in related_courses:
            by_difficulty[course.difficulty].append(course)

        # 학습 경로 생성
        path = []

        # 1단계: 초급
        if by_difficulty["beginner"]:
            beginner_sorted = sorted(
                by_difficulty["beginner"],
                key=lambda x: x.completion_rate, reverse=True
            )
            path.append({
                "stage": 1,
                "stage_name": "기초 다지기",
                "difficulty": "beginner",
                "courses": [
                    {
                        "course_id": c.course_id,
                        "title": c.title,
                        "completion_rate": c.completion_rate
                    }
                    for c in beginner_sorted[:3]
                ]
            })

        # 2단계: 중급
        if by_difficulty["intermediate"]:
            intermediate_sorted = sorted(
                by_difficulty["intermediate"],
                key=lambda x: x.completion_rate, reverse=True
            )
            path.append({
                "stage": 2,
                "stage_name": "실력 향상",
                "difficulty": "intermediate",
                "courses": [
                    {
                        "course_id": c.course_id,
                        "title": c.title,
                        "completion_rate": c.completion_rate
                    }
                    for c in intermediate_sorted[:3]
                ]
            })

        # 3단계: 고급
        if by_difficulty["advanced"]:
            advanced_sorted = sorted(
                by_difficulty["advanced"],
                key=lambda x: x.completion_rate, reverse=True
            )
            path.append({
                "stage": 3,
                "stage_name": "전문가 도전",
                "difficulty": "advanced",
                "courses": [
                    {
                        "course_id": c.course_id,
                        "title": c.title,
                        "completion_rate": c.completion_rate
                    }
                    for c in advanced_sorted[:2]
                ]
            })

        return path


# 테스트
if __name__ == "__main__":
    recommender = CourseRecommender(seed=42)

    # 테스트 사용자 프로필
    test_profile = UserProfile(
        user_id="test_user",
        level=UserLevel.BEGINNER,
        desired_role=JobRole.BACKEND,
        known_concepts=[BasicConcept.VARIABLE, BasicConcept.LOOP],
        completed_courses=["course_001"],
        in_progress_courses=[]
    )

    print("=== 규칙 기반 추천 ===")
    rule_recs = recommender.recommend_rule_based(test_profile, limit=3)
    for rec in rule_recs:
        print(f"{rec['title']} (점수: {rec['recommendation_score']})")
        print(f"  이유: {', '.join(rec['reasons'])}")

    print("\n=== 협업 필터링 추천 ===")
    collab_recs = recommender.recommend_collaborative(
        "test_user",
        ["course_001"],
        limit=3
    )
    for rec in collab_recs:
        print(f"{rec['title']} (유사도: {rec['similarity_score']})")

    print("\n=== 하이브리드 추천 ===")
    hybrid_recs = recommender.recommend_hybrid(test_profile, limit=3)
    for rec in hybrid_recs:
        print(f"{rec['title']} (최종점수: {rec['final_score']})")

    print("\n=== 맞춤 학습 경로 ===")
    path = recommender.get_personalized_path(test_profile)
    for stage in path:
        print(f"[{stage['stage_name']}]")
        for c in stage['courses']:
            print(f"  - {c['title']}")
