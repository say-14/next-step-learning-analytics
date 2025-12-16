import { useState } from 'react'
import NavLinks from '../components/NavLinks'
import ErrorMessage from '../components/ErrorMessage'
import { userApi } from '../services/api'
import type { LevelTestRequest, LevelTestResponse } from '../types'
import styles from './LevelTestPage.module.css'

const LEVEL_NAMES: Record<string, string> = {
  absolute_beginner: '완전 초보',
  beginner: '초보',
  junior_ready: '신입 준비 완료',
  data_focused: '데이터 특화',
  web_focused: '웹 개발 특화',
  ai_focused: 'AI 특화',
  intermediate: '중급',
}

const CONCEPTS = [
  { value: 'variable', label: '변수와 데이터 타입' },
  { value: 'loop', label: '반복문 (for, while)' },
  { value: 'function', label: '함수' },
  { value: 'http', label: 'HTTP/웹 기초' },
  { value: 'database', label: '데이터베이스/SQL' },
  { value: 'git', label: 'Git 버전 관리' },
  { value: 'algorithm', label: '알고리즘 기초' },
  { value: 'oop', label: '객체지향 프로그래밍' },
]

const LevelTestPage = () => {
  const [formData, setFormData] = useState<LevelTestRequest>({
    education: '',
    daily_study_hours: 3,
    known_concepts: [],
    desired_role: '',
    has_project_experience: false,
    coding_months: 0,
  })
  const [result, setResult] = useState<LevelTestResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const handleConceptChange = (concept: string, checked: boolean) => {
    setFormData((prev) => ({
      ...prev,
      known_concepts: checked
        ? [...prev.known_concepts, concept]
        : prev.known_concepts.filter((c) => c !== concept),
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const response = await userApi.estimateLevel(formData)
      setResult(response)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('레벨 분석 중 오류가 발생했습니다.')
      setError(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <NavLinks variant="light" />
      <h1 className={styles.title}>🎯 개발자 레벨 테스트</h1>

      <div className={styles.card}>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label className={styles.label}>📚 학력/전공</label>
            <select
              className={styles.select}
              value={formData.education}
              onChange={(e) => setFormData((prev) => ({ ...prev, education: e.target.value }))}
              required
            >
              <option value="">선택하세요</option>
              <option value="high_school">고등학교 졸업</option>
              <option value="college">전문대 졸업</option>
              <option value="university_non_cs">4년제 (비전공)</option>
              <option value="university_cs">4년제 (CS/IT 전공)</option>
              <option value="graduate">대학원</option>
              <option value="bootcamp">부트캠프 수료</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>⏰ 하루 공부 가능 시간</label>
            <input
              type="number"
              className={styles.input}
              min="0"
              max="24"
              step="0.5"
              value={formData.daily_study_hours}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, daily_study_hours: parseFloat(e.target.value) }))
              }
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>💻 알고 있는 기초 개념 (해당하는 것 모두 선택)</label>
            <div className={styles.checkboxGroup}>
              {CONCEPTS.map((concept) => (
                <label key={concept.value} className={styles.checkboxItem}>
                  <input
                    type="checkbox"
                    checked={formData.known_concepts.includes(concept.value)}
                    onChange={(e) => handleConceptChange(concept.value, e.target.checked)}
                  />
                  {concept.label}
                </label>
              ))}
            </div>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>🎯 희망 직무</label>
            <select
              className={styles.select}
              value={formData.desired_role}
              onChange={(e) => setFormData((prev) => ({ ...prev, desired_role: e.target.value }))}
              required
            >
              <option value="">선택하세요</option>
              <option value="backend">백엔드 개발</option>
              <option value="frontend">프론트엔드 개발</option>
              <option value="data">데이터 분석/사이언스</option>
              <option value="ai">AI/머신러닝</option>
              <option value="fullstack">풀스택 개발</option>
              <option value="devops">DevOps/인프라</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>🛠️ 프로젝트 경험</label>
            <select
              className={styles.select}
              value={formData.has_project_experience ? 'true' : 'false'}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, has_project_experience: e.target.value === 'true' }))
              }
            >
              <option value="false">없음</option>
              <option value="true">있음</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>📅 코딩 경험 (개월)</label>
            <input
              type="number"
              className={styles.input}
              min="0"
              value={formData.coding_months}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, coding_months: parseInt(e.target.value) || 0 }))
              }
            />
          </div>

          <button type="submit" className={styles.submitBtn} disabled={loading}>
            {loading ? '분석 중...' : '레벨 분석하기'}
          </button>
        </form>

        {error && (
          <ErrorMessage
            message={error.message}
            onRetry={() => handleSubmit({ preventDefault: () => {} } as React.FormEvent)}
            compact
          />
        )}

        {result && (
          <div className={styles.result}>
            <div className={styles.levelBadge}>
              {LEVEL_NAMES[result.estimated_level] || result.estimated_level}
            </div>
            <p className={styles.confidence}>신뢰도: {(result.confidence_score * 100).toFixed(0)}%</p>
            <p className={styles.levelDesc}>{result.level_description}</p>

            <h4 className={styles.sectionTitle}>📚 추천 학습 경로</h4>
            <ol className={styles.pathList}>
              {result.recommended_path.map((path, index) => (
                <li key={index}>{path}</li>
              ))}
            </ol>

            <h4 className={styles.sectionTitle}>✅ 강점</h4>
            <ul className={`${styles.strengthList} ${styles.positive}`}>
              {result.strengths.map((strength, index) => (
                <li key={index}>{strength}</li>
              ))}
            </ul>

            <h4 className={styles.sectionTitle}>📝 개선 필요</h4>
            <ul className={`${styles.strengthList} ${styles.negative}`}>
              {result.areas_to_improve.map((area, index) => (
                <li key={index}>{area}</li>
              ))}
            </ul>

            <div className={styles.timeEstimate}>
              예상 취업 준비 기간: {result.estimated_time_to_job_ready}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default LevelTestPage
