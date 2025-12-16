"""
시드 데이터 생성 스크립트
PostgreSQL에 테스트 데이터 삽입
"""
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
from datetime import datetime, timedelta
from database import SessionLocal, engine
from models.db_models import Base, User, Course, Enrollment, LearningLog

# 시드 고정 (재현성)
random.seed(42)


def create_tables():
    """테이블 생성"""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created!")


def seed_users(db, count: int = 500) -> list[User]:
    """사용자 데이터 생성"""
    print(f"Seeding {count} users...")

    levels = ["absolute_beginner", "beginner", "junior_ready", "intermediate"]
    users = []

    for i in range(1, count + 1):
        user = User(
            user_code=f"U{i:05d}",
            username=f"학습자{i}",
            email=f"user{i}@example.com",
            level=random.choice(levels)
        )
        users.append(user)

    db.bulk_save_objects(users)
    db.commit()
    print(f"  -> {count} users created!")
    return db.query(User).all()


def seed_courses(db) -> list[Course]:
    """강의 데이터 생성"""
    print("Seeding courses...")

    courses_data = [
        {"code": "PY001", "title": "Python 기초 완성", "category": "python", "difficulty": "beginner", "duration": 600, "instructor": "김파이썬"},
        {"code": "PY002", "title": "Python 중급: 객체지향", "category": "python", "difficulty": "intermediate", "duration": 480, "instructor": "김파이썬"},
        {"code": "FA001", "title": "FastAPI 마스터", "category": "web_backend", "difficulty": "intermediate", "duration": 720, "instructor": "이백엔드"},
        {"code": "DJ001", "title": "Django 웹 개발", "category": "web_backend", "difficulty": "intermediate", "duration": 900, "instructor": "이백엔드"},
        {"code": "DA001", "title": "데이터 분석 입문", "category": "data_analysis", "difficulty": "beginner", "duration": 540, "instructor": "박데이터"},
        {"code": "DA002", "title": "Pandas 완벽 가이드", "category": "data_analysis", "difficulty": "intermediate", "duration": 480, "instructor": "박데이터"},
        {"code": "ML001", "title": "머신러닝 기초", "category": "machine_learning", "difficulty": "intermediate", "duration": 840, "instructor": "최인공"},
        {"code": "ML002", "title": "딥러닝 입문", "category": "machine_learning", "difficulty": "advanced", "duration": 960, "instructor": "최인공"},
        {"code": "DB001", "title": "SQL 데이터베이스 마스터", "category": "database", "difficulty": "beginner", "duration": 600, "instructor": "정디비"},
        {"code": "DB002", "title": "PostgreSQL 고급 기법", "category": "database", "difficulty": "advanced", "duration": 720, "instructor": "정디비"},
        {"code": "RE001", "title": "React 프론트엔드", "category": "web_frontend", "difficulty": "intermediate", "duration": 780, "instructor": "한프론트"},
        {"code": "AL001", "title": "알고리즘 문제풀이", "category": "algorithm", "difficulty": "intermediate", "duration": 1200, "instructor": "강알고"},
    ]

    courses = []
    for c in courses_data:
        course = Course(
            course_code=c["code"],
            title=c["title"],
            category=c["category"],
            difficulty=c["difficulty"],
            duration_minutes=c["duration"],
            instructor=c["instructor"],
            tags=["인기", "추천"] if random.random() > 0.5 else []
        )
        courses.append(course)

    db.bulk_save_objects(courses)
    db.commit()
    print(f"  -> {len(courses)} courses created!")
    return db.query(Course).all()


# 이탈 확률 (구간별)
DROPOUT_PROBABILITY = {
    (0, 10): 0.25,
    (10, 20): 0.15,
    (20, 30): 0.12,
    (30, 40): 0.10,
    (40, 50): 0.08,
    (50, 60): 0.06,
    (60, 70): 0.05,
    (70, 80): 0.04,
    (80, 90): 0.03,
    (90, 100): 0.02,
}


def get_dropout_probability(progress: float) -> float:
    for (start, end), prob in DROPOUT_PROBABILITY.items():
        if start <= progress < end:
            return prob
    return 0.02


def get_dropout_reason(progress: float) -> str:
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


def seed_enrollments_and_logs(db, users: list[User], courses: list[Course]):
    """수강 신청 및 학습 로그 생성"""
    print("Seeding enrollments and learning logs...")

    enrollments = []
    logs = []

    for user in users:
        # 각 사용자는 1~4개 강의 수강
        num_courses = random.randint(1, 4)
        selected_courses = random.sample(courses, num_courses)

        for course in selected_courses:
            # 수강 신청
            start_date = datetime.now() - timedelta(days=random.randint(1, 90))
            enrollment = Enrollment(
                user_id=user.id,
                course_id=course.id,
                status="active",
                enrolled_at=start_date
            )

            # 학습 시뮬레이션
            current_progress = 0.0
            current_time = start_date
            user_logs = []
            is_dropped = False

            while current_progress < 100:
                dropout_prob = get_dropout_probability(current_progress)

                if random.random() < dropout_prob:
                    # 이탈
                    user_logs.append({
                        "user_id": user.id,
                        "course_id": course.id,
                        "progress_percent": round(current_progress, 1),
                        "watch_duration_sec": random.randint(60, 600),
                        "is_dropout": True,
                        "dropout_reason": get_dropout_reason(current_progress),
                        "logged_at": current_time
                    })
                    enrollment.status = "dropped"
                    enrollment.dropped_at = current_time
                    enrollment.progress_percent = current_progress
                    is_dropped = True
                    break

                # 정상 학습
                progress_increment = random.uniform(2, 8)
                watch_duration = int((progress_increment / 100) * course.duration_minutes * 60)

                new_progress = min(current_progress + progress_increment, 100)
                user_logs.append({
                    "user_id": user.id,
                    "course_id": course.id,
                    "progress_percent": round(new_progress, 1),
                    "watch_duration_sec": watch_duration,
                    "is_dropout": False,
                    "dropout_reason": None,
                    "logged_at": current_time
                })

                current_progress = new_progress
                current_time += timedelta(hours=random.randint(1, 72))

            # 완강 처리
            if not is_dropped and current_progress >= 100:
                enrollment.status = "completed"
                enrollment.completed_at = current_time
                enrollment.progress_percent = 100.0

            enrollments.append(enrollment)
            logs.extend(user_logs)

    # 벌크 인서트
    db.bulk_save_objects(enrollments)
    db.commit()
    print(f"  -> {len(enrollments)} enrollments created!")

    # 로그는 배치로 삽입 (대량 데이터)
    batch_size = 1000
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i+batch_size]
        db.bulk_insert_mappings(LearningLog, batch)
        db.commit()
        print(f"  -> Inserted logs {i} ~ {min(i+batch_size, len(logs))}")

    print(f"  -> Total {len(logs)} learning logs created!")


def main():
    print("=" * 50)
    print("Education DB Seed Script")
    print("=" * 50)

    db = SessionLocal()

    try:
        # 1. 테이블 생성
        create_tables()

        # 2. 기존 데이터 확인
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"\nWarning: Database already has {existing_users} users.")
            confirm = input("Clear existing data? (y/N): ")
            if confirm.lower() == 'y':
                print("Clearing data...")
                db.query(LearningLog).delete()
                db.query(Enrollment).delete()
                db.query(Course).delete()
                db.query(User).delete()
                db.commit()
                print("Data cleared!")
            else:
                print("Aborted.")
                return

        # 3. 시드 데이터 생성
        users = seed_users(db, count=500)
        courses = seed_courses(db)
        seed_enrollments_and_logs(db, users, courses)

        print("\n" + "=" * 50)
        print("Seed completed successfully!")
        print("=" * 50)

        # 4. 통계 출력
        print("\nDatabase Statistics:")
        print(f"  - Users: {db.query(User).count()}")
        print(f"  - Courses: {db.query(Course).count()}")
        print(f"  - Enrollments: {db.query(Enrollment).count()}")
        print(f"  - Learning Logs: {db.query(LearningLog).count()}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
