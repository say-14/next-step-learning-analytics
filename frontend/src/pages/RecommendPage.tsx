import { useState } from 'react'
import NavLinks from '../components/NavLinks'
import ErrorMessage from '../components/ErrorMessage'
import { recommendApi } from '../services/api'
import type { Recommendation, LearningPathStage, PopularCourse } from '../types'
import styles from './RecommendPage.module.css'

type TabType = 'quick' | 'path' | 'popular'

const STAGE_NAMES: Record<string, string> = {
  beginner: '초급',
  intermediate: '중급',
  advanced: '고급',
}

const RecommendPage = () => {
  const [activeTab, setActiveTab] = useState<TabType>('quick')
  const [role, setRole] = useState('backend')
  const [level, setLevel] = useState('beginner')
  const [pathRole, setPathRole] = useState('backend')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [learningPath, setLearningPath] = useState<LearningPathStage[]>([])
  const [popularCourses, setPopularCourses] = useState<PopularCourse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const switchTab = (tab: TabType) => {
    setActiveTab(tab)
    setRecommendations([])
    setLearningPath([])
    setPopularCourses([])
    setError(null)
  }

  const getRecommendations = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await recommendApi.getQuickRecommendations({
        desired_role: role,
        experience_level: level,
        completed_courses: [],
      })
      setRecommendations(data.recommendations)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('추천 목록을 불러오는데 실패했습니다.')
      setError(error)
      console.error('Failed to get recommendations:', err)
    } finally {
      setLoading(false)
    }
  }

  const getLearningPath = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await recommendApi.getLearningPath({
        user_id: 'web_user',
        level: 'beginner',
        desired_role: pathRole,
        known_concepts: [],
        completed_courses: [],
        in_progress_courses: [],
      })
      setLearningPath(data.learning_path)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('학습 경로를 불러오는데 실패했습니다.')
      setError(error)
      console.error('Failed to get learning path:', err)
    } finally {
      setLoading(false)
    }
  }

  const getPopularCourses = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await recommendApi.getPopularCourses(6)
      setPopularCourses(data.courses)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('인기 강의를 불러오는데 실패했습니다.')
      setError(error)
      console.error('Failed to get popular courses:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <NavLinks variant="light" />
      <h1 className={styles.title}>🎯 맞춤 강의 추천</h1>

      <div className={styles.card}>
        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${activeTab === 'quick' ? styles.active : ''}`}
            onClick={() => switchTab('quick')}
          >
            빠른 추천
          </button>
          <button
            className={`${styles.tab} ${activeTab === 'path' ? styles.active : ''}`}
            onClick={() => switchTab('path')}
          >
            학습 경로
          </button>
          <button
            className={`${styles.tab} ${activeTab === 'popular' ? styles.active : ''}`}
            onClick={() => switchTab('popular')}
          >
            인기 강의
          </button>
        </div>

        {activeTab === 'quick' && (
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.label}>희망 직무</label>
              <select className={styles.select} value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="backend">백엔드 개발</option>
                <option value="frontend">프론트엔드 개발</option>
                <option value="data">데이터 분석</option>
                <option value="ai">AI/머신러닝</option>
                <option value="fullstack">풀스택 개발</option>
                <option value="devops">DevOps</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>경험 수준</label>
              <select className={styles.select} value={level} onChange={(e) => setLevel(e.target.value)}>
                <option value="beginner">초보</option>
                <option value="intermediate">중급</option>
                <option value="advanced">고급</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <button className={styles.submitBtn} onClick={getRecommendations} disabled={loading}>
                {loading ? '로딩 중...' : '추천받기'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'path' && (
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.label}>희망 직무</label>
              <select
                className={styles.select}
                value={pathRole}
                onChange={(e) => setPathRole(e.target.value)}
              >
                <option value="backend">백엔드 개발</option>
                <option value="frontend">프론트엔드 개발</option>
                <option value="data">데이터 분석</option>
                <option value="ai">AI/머신러닝</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <button className={styles.submitBtn} onClick={getLearningPath} disabled={loading}>
                {loading ? '로딩 중...' : '경로 생성'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'popular' && (
          <button className={styles.submitBtn} onClick={getPopularCourses} disabled={loading}>
            {loading ? '로딩 중...' : '인기 강의 보기'}
          </button>
        )}

        {error && (
          <ErrorMessage
            message={error.message}
            onRetry={
              activeTab === 'quick'
                ? getRecommendations
                : activeTab === 'path'
                  ? getLearningPath
                  : getPopularCourses
            }
            compact
          />
        )}

        <div className={styles.results}>
          {recommendations.length > 0 && (
            <div className={styles.recommendations}>
              {recommendations.map((rec) => (
                <div key={rec.course_id} className={styles.recCard}>
                  <div className={styles.recTitle}>{rec.title}</div>
                  <div className={styles.recMeta}>
                    <span className={styles.recBadge}>{rec.category}</span>
                    <span className={styles.recBadge}>{rec.difficulty}</span>
                  </div>
                  <div className={styles.recScore}>
                    추천 점수: {rec.recommendation_score} | 완강률: {rec.completion_rate}%
                  </div>
                  <div className={styles.recReasons}>
                    {rec.reasons.map((reason, index) => (
                      <div key={index} className={styles.recReason}>
                        ✓ {reason}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {learningPath.length > 0 && (
            <div className={styles.learningPath}>
              {learningPath.map((stage) => (
                <div key={stage.stage} className={styles.pathStage}>
                  <div className={styles.stageHeader}>
                    <div className={styles.stageNumber}>{stage.stage}</div>
                    <div>
                      <strong>{stage.stage_name}</strong>
                      <span className={styles.stageDifficulty}>
                        ({STAGE_NAMES[stage.difficulty] || stage.difficulty})
                      </span>
                    </div>
                  </div>
                  <div className={styles.stageCourses}>
                    {stage.courses.map((course) => (
                      <div key={course.course_id} className={styles.stageCourse}>
                        <div className={styles.stageCourseTitle}>{course.title}</div>
                        <div className={styles.stageCourseRate}>완강률 {course.completion_rate}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {popularCourses.length > 0 && (
            <div className={styles.recommendations}>
              {popularCourses.map((course) => (
                <div key={course.course_id} className={styles.recCard}>
                  <div className={styles.recTitle}>{course.title}</div>
                  <div className={styles.recMeta}>
                    <span className={styles.recBadge}>{course.category}</span>
                    <span className={styles.recBadge}>{course.difficulty}</span>
                  </div>
                  <div className={styles.recScore}>
                    수강생: {course.total_enrollments.toLocaleString()}명 | 완강률: {course.completion_rate}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default RecommendPage
