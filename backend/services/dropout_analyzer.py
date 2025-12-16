"""
이탈 구간 분석 서비스
학습 로그를 분석하여 이탈 패턴을 파악
"""
from collections import defaultdict
from typing import Optional
import statistics


class DropoutAnalyzer:
    """이탈 구간 분석기"""

    # 구간 설정 (10% 단위)
    SEGMENTS = [(i, i + 10) for i in range(0, 100, 10)]

    # 위험도 기준
    RISK_THRESHOLDS = {
        "critical": 20,  # 20% 이상 이탈
        "high": 15,      # 15% 이상
        "medium": 10,    # 10% 이상
        "low": 0         # 그 외
    }

    def __init__(self):
        self.logs = []
        self.dropout_points = []

    def load_logs(self, logs: list[dict]):
        """학습 로그 데이터 로드"""
        self.logs = logs
        self._extract_dropout_points()

    def _extract_dropout_points(self):
        """이탈 지점 추출"""
        self.dropout_points = []

        # 사용자별 마지막 로그 추적
        user_last_log = {}

        for log in self.logs:
            user_id = log["user_id"]
            user_last_log[user_id] = log

        # 이탈한 사용자 추출 (완료하지 않은 사용자)
        for user_id, last_log in user_last_log.items():
            if last_log.get("is_dropout", False) or \
               (not last_log.get("is_completed", False) and last_log["progress_percent"] < 100):
                self.dropout_points.append({
                    "user_id": user_id,
                    "course_id": last_log["course_id"],
                    "dropout_percent": last_log["progress_percent"],
                    "reason": last_log.get("dropout_reason", "미확인")
                })

    def analyze_segments(self, course_id: Optional[str] = None) -> list[dict]:
        """
        구간별 이탈 분석

        Returns:
            list[dict]: 구간별 분석 결과
        """
        # 해당 강의의 이탈 포인트만 필터링
        dropouts = self.dropout_points
        if course_id:
            dropouts = [d for d in dropouts if d["course_id"] == course_id]

        total_dropouts = len(dropouts)
        if total_dropouts == 0:
            return self._empty_segment_result()

        # 구간별 카운트
        segment_counts = defaultdict(int)

        for dropout in dropouts:
            percent = dropout["dropout_percent"]
            for start, end in self.SEGMENTS:
                if start <= percent < end:
                    segment_counts[(start, end)] += 1
                    break

        # 결과 생성
        results = []
        for start, end in self.SEGMENTS:
            count = segment_counts[(start, end)]
            rate = (count / total_dropouts * 100) if total_dropouts > 0 else 0
            risk_level = self._get_risk_level(rate)

            results.append({
                "segment_start": start,
                "segment_end": end,
                "segment_label": f"{start}-{end}%",
                "dropout_count": count,
                "dropout_rate": round(rate, 1),
                "risk_level": risk_level,
                "risk_color": self._get_risk_color(risk_level)
            })

        return results

    def get_danger_zones(self, course_id: Optional[str] = None, threshold: float = 15.0) -> list[dict]:
        """
        위험 구간(이탈률 높은 구간) 추출

        Args:
            threshold: 위험으로 판단할 이탈률 기준 (%)
        """
        segments = self.analyze_segments(course_id)

        danger_zones = []
        for seg in segments:
            if seg["dropout_rate"] >= threshold:
                danger_zones.append({
                    "segment": seg["segment_label"],
                    "dropout_rate": seg["dropout_rate"],
                    "risk_level": seg["risk_level"],
                    "recommendation": self._get_recommendation(
                        seg["segment_start"],
                        seg["dropout_rate"]
                    )
                })

        return sorted(danger_zones, key=lambda x: x["dropout_rate"], reverse=True)

    def get_dropout_reasons(self, course_id: Optional[str] = None) -> dict:
        """이탈 사유 분석"""
        dropouts = self.dropout_points
        if course_id:
            dropouts = [d for d in dropouts if d["course_id"] == course_id]

        reason_counts = defaultdict(int)
        for dropout in dropouts:
            reason = dropout.get("reason", "미확인")
            reason_counts[reason] += 1

        total = sum(reason_counts.values())
        return {
            "reasons": [
                {
                    "reason": reason,
                    "count": count,
                    "percentage": round(count / total * 100, 1) if total > 0 else 0
                }
                for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
            ],
            "total_dropouts": total
        }

    def get_course_summary(self, course_id: str, total_enrollments: int) -> dict:
        """강의별 전체 요약 통계"""
        segments = self.analyze_segments(course_id)
        danger_zones = self.get_danger_zones(course_id)
        reasons = self.get_dropout_reasons(course_id)

        total_dropouts = reasons["total_dropouts"]
        completion_rate = ((total_enrollments - total_dropouts) / total_enrollments * 100) \
            if total_enrollments > 0 else 0

        # 평균 이탈 지점 계산
        course_dropouts = [d for d in self.dropout_points if d["course_id"] == course_id]
        avg_dropout_point = statistics.mean([d["dropout_percent"] for d in course_dropouts]) \
            if course_dropouts else 0

        return {
            "course_id": course_id,
            "total_enrollments": total_enrollments,
            "total_dropouts": total_dropouts,
            "overall_dropout_rate": round(total_dropouts / total_enrollments * 100, 1) \
                if total_enrollments > 0 else 0,
            "completion_rate": round(completion_rate, 1),
            "average_dropout_point": round(avg_dropout_point, 1),
            "segments": segments,
            "danger_zones": danger_zones,
            "dropout_reasons": reasons["reasons"][:5]  # 상위 5개 사유
        }

    def get_chart_data(self, course_id: Optional[str] = None) -> dict:
        """Chart.js용 데이터 포맷"""
        segments = self.analyze_segments(course_id)

        return {
            "labels": [seg["segment_label"] for seg in segments],
            "datasets": [
                {
                    "label": "이탈자 수",
                    "data": [seg["dropout_count"] for seg in segments],
                    "backgroundColor": [seg["risk_color"] for seg in segments],
                    "borderColor": [seg["risk_color"] for seg in segments],
                    "borderWidth": 1
                }
            ],
            "dropout_rates": [seg["dropout_rate"] for seg in segments]
        }

    def _get_risk_level(self, rate: float) -> str:
        """이탈률에 따른 위험도 반환"""
        for level, threshold in self.RISK_THRESHOLDS.items():
            if rate >= threshold:
                return level
        return "low"

    def _get_risk_color(self, level: str) -> str:
        """위험도별 색상"""
        colors = {
            "critical": "#dc3545",  # 빨강
            "high": "#fd7e14",      # 주황
            "medium": "#ffc107",    # 노랑
            "low": "#28a745"        # 초록
        }
        return colors.get(level, "#6c757d")

    def _get_recommendation(self, segment_start: int, dropout_rate: float) -> str:
        """구간별 개선 추천"""
        recommendations = {
            0: "강의 소개/미리보기 개선, 선수 지식 명확히 안내",
            10: "초반 난이도 조절, 기초 개념 보충 자료 제공",
            20: "중간 점검 퀴즈 추가, 실습 예제 강화",
            30: "학습 리마인더 발송, 마일스톤 보상 제공",
            40: "절반 완료 축하 메시지, 후반부 미리보기 제공",
            50: "학습 커뮤니티 연결, 1:1 질문 기회 제공",
            60: "프로젝트 과제 도입, 실전 응용 사례 추가",
            70: "완주 인증서 미리보기, 수강 후기 작성 유도",
            80: "마지막 스퍼트 격려, 복습 가이드 제공",
            90: "완강 축하 준비, 다음 강의 추천 안내"
        }
        return recommendations.get(segment_start, "콘텐츠 품질 점검 필요")

    def _empty_segment_result(self) -> list[dict]:
        """이탈 데이터가 없을 때 빈 결과"""
        return [
            {
                "segment_start": start,
                "segment_end": end,
                "segment_label": f"{start}-{end}%",
                "dropout_count": 0,
                "dropout_rate": 0.0,
                "risk_level": "low",
                "risk_color": "#28a745"
            }
            for start, end in self.SEGMENTS
        ]


# 테스트
if __name__ == "__main__":
    from data_generator import LearningDataGenerator

    # 데이터 생성
    generator = LearningDataGenerator(seed=42)
    logs = generator.generate_course_logs("course_001", num_users=100)

    # 분석
    analyzer = DropoutAnalyzer()
    analyzer.load_logs(logs)

    print("=== 구간별 이탈 분석 ===")
    segments = analyzer.analyze_segments("course_001")
    for seg in segments:
        print(f"{seg['segment_label']}: {seg['dropout_count']}명 ({seg['dropout_rate']}%) - {seg['risk_level']}")

    print("\n=== 위험 구간 ===")
    dangers = analyzer.get_danger_zones("course_001")
    for d in dangers:
        print(f"{d['segment']}: {d['dropout_rate']}% - {d['recommendation']}")

    print("\n=== 전체 요약 ===")
    summary = analyzer.get_course_summary("course_001", 100)
    print(f"완강률: {summary['completion_rate']}%")
    print(f"평균 이탈 지점: {summary['average_dropout_point']}%")
