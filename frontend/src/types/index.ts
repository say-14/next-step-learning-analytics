// Analysis Types
export interface Course {
  course_id: string
  title: string
  completion_rate: number
  dropout_rate: number
}

export interface CoursesResponse {
  courses: Course[]
}

export interface Summary {
  total_enrollments: number
  overall_dropout_rate: number
  completion_rate: number
  average_dropout_point: number
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor: string[]
  borderColor: string[]
}

export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
  dropout_counts: number[]
}

export interface DangerZone {
  segment: string
  dropout_rate: number
  risk_level: string
  recommendation: string
}

export interface DangerZonesResponse {
  danger_zones: DangerZone[]
}

export interface DropoutReason {
  reason: string
  count: number
  percentage?: number
}

export interface ReasonsResponse {
  reasons: DropoutReason[]
}

// User/Level Test Types
export interface LevelTestRequest {
  education: string
  daily_study_hours: number
  known_concepts: string[]
  desired_role: string
  has_project_experience: boolean
  coding_months: number
}

export interface LevelTestResponse {
  estimated_level: string
  confidence_score: number
  level_description: string
  recommended_path: string[]
  strengths: string[]
  areas_to_improve: string[]
  estimated_time_to_job_ready: string
}

// Course Detail Types
export interface CourseListItem {
  course_id: string
  title: string
  difficulty: string
  completion_rate: number
}

export interface FunnelStep {
  stage: string
  count: number
  rate: number
}

export interface ComparisonMetric {
  value: number
  diff: number
  is_above_average: boolean
}

export interface CourseDetail {
  course_id: string
  title: string
  enrollment_metrics: {
    total_enrollments: number
    watched_at_least_once: number
  }
  progress_metrics: {
    reached_50_percent: number
    completed: number
  }
  funnel_data: FunnelStep[]
  comparison_with_average: {
    completion_rate: ComparisonMetric
    dropout_rate: ComparisonMetric
  }
  dropout_metrics: {
    total_dropouts: number
    average_dropout_point: number
    peak_dropout_segment: string
    peak_dropout_rate: number
  }
  engagement_metrics: {
    average_watch_time_minutes: number
    average_days_to_complete: number
  }
}

// Recommend Types
export interface QuickRecommendRequest {
  desired_role: string
  experience_level: string
  completed_courses: string[]
}

export interface Recommendation {
  course_id: string
  title: string
  category: string
  difficulty: string
  recommendation_score: number
  completion_rate: number
  reasons: string[]
}

export interface RecommendationsResponse {
  recommendations: Recommendation[]
}

export interface LearningPathRequest {
  user_id: string
  level: string
  desired_role: string
  known_concepts: string[]
  completed_courses: string[]
  in_progress_courses: string[]
}

export interface LearningPathCourse {
  course_id: string
  title: string
  completion_rate: number
}

export interface LearningPathStage {
  stage: number
  stage_name: string
  difficulty: string
  courses: LearningPathCourse[]
}

export interface LearningPathResponse {
  learning_path: LearningPathStage[]
}

export interface PopularCourse {
  course_id: string
  title: string
  category: string
  difficulty: string
  total_enrollments: number
  completion_rate: number
}

export interface PopularCoursesResponse {
  courses: PopularCourse[]
}
