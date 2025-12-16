import type {
  CoursesResponse,
  Summary,
  ChartData,
  DangerZonesResponse,
  ReasonsResponse,
  LevelTestRequest,
  LevelTestResponse,
  CourseListItem,
  CourseDetail,
  QuickRecommendRequest,
  RecommendationsResponse,
  LearningPathRequest,
  LearningPathResponse,
  PopularCoursesResponse,
} from '../types'

const API_BASE = '/api'

// API 에러 클래스
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// 공통 fetch 래퍼
async function fetchApi<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)

  if (!response.ok) {
    throw new ApiError(
      `API 요청 실패: ${response.statusText}`,
      response.status,
      response.statusText
    )
  }

  const data = await response.json()
  return data as T
}

// Analysis API
export const analysisApi = {
  getCourses: (): Promise<CoursesResponse> =>
    fetchApi(`${API_BASE}/analysis/courses`),

  getSummary: (courseId: string): Promise<Summary> =>
    fetchApi(`${API_BASE}/analysis/summary/${courseId}`),

  getChartData: (courseId: string): Promise<ChartData> =>
    fetchApi(`${API_BASE}/analysis/chart-data/${courseId}`),

  getDangerZones: (courseId: string, threshold = 10): Promise<DangerZonesResponse> =>
    fetchApi(`${API_BASE}/analysis/danger-zones/${courseId}?threshold=${threshold}`),

  getReasons: (courseId: string): Promise<ReasonsResponse> =>
    fetchApi(`${API_BASE}/analysis/reasons/${courseId}`),
}

// User API
export const userApi = {
  estimateLevel: (data: LevelTestRequest): Promise<LevelTestResponse> =>
    fetchApi(`${API_BASE}/user/estimate-level`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
}

// Courses API
export const coursesApi = {
  getList: (): Promise<CourseListItem[]> =>
    fetchApi(`${API_BASE}/courses/`),

  getDetail: (courseId: string): Promise<CourseDetail> =>
    fetchApi(`${API_BASE}/courses/detail/${courseId}`),
}

// Recommend API
export const recommendApi = {
  getQuickRecommendations: (data: QuickRecommendRequest): Promise<RecommendationsResponse> =>
    fetchApi(`${API_BASE}/recommend/quick`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  getLearningPath: (data: LearningPathRequest): Promise<LearningPathResponse> =>
    fetchApi(`${API_BASE}/recommend/learning-path`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  getPopularCourses: (limit = 6): Promise<PopularCoursesResponse> =>
    fetchApi(`${API_BASE}/recommend/popular?limit=${limit}`),
}
