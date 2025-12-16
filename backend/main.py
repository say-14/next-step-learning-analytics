"""
이탈 구간 분석 - FastAPI 메인 애플리케이션
"""
import sys
from pathlib import Path


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 프로젝트 루트 path 추가 (필요하면)
sys.path.insert(0, str(Path(__file__).parent))

from routers.analysis import router as analysis_router
from routers.user import router as user_router
from routers.course_detail import router as course_detail_router
from routers.recommend import router as recommend_router
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="학습 이탈 구간 분석 API",
    description="온라인 강의 학습자의 이탈 패턴을 분석하는 API",
    version="1.0.0",
)

@app.get("/", include_in_schema=False)
async def root_redirect():
    # 프론트 개발 서버로 리다이렉트
    return RedirectResponse(url="http://localhost:5173/")


# CORS 설정
# Vite dev 서버가 보통 http://localhost:5173 이라서 여기를 허용
origins = [
    "http://localhost:5173",  # Vite 개발서버
    "http://127.0.0.1:5173",
    # 나중에 배포 시 프론트 도메인 추가 (예: "https://my-learning-analytics.com")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(analysis_router, prefix="/api/analysis",tags=["analysis"])
app.include_router(user_router, prefix="/api/user",tags=["user"])
app.include_router(course_detail_router, prefix="/api/courses",tags=["courses"])
app.include_router(recommend_router, prefix="/api/recommend",tags=["recommend"])



# 헬스 체크
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn


    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
