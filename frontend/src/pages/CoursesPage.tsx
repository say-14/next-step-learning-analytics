import { useState, useEffect } from 'react'
import { Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import NavLinks from '../components/NavLinks'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import { coursesApi } from '../services/api'
import type { CourseListItem, CourseDetail } from '../types'
import styles from './CoursesPage.module.css'

ChartJS.register(ArcElement, Tooltip, Legend)

const CoursesPage = () => {
  const [courses, setCourses] = useState<CourseListItem[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null)
  const [detail, setDetail] = useState<CourseDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    loadCourses()
  }, [])

  const loadCourses = async () => {
    try {
      setError(null)
      const data = await coursesApi.getList()
      setCourses(data)
      if (data.length > 0) {
        selectCourse(data[0].course_id)
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('강의 목록을 불러오는데 실패했습니다.')
      setError(error)
      console.error('Failed to load courses:', err)
    } finally {
      setLoading(false)
    }
  }

  const selectCourse = async (courseId: string) => {
    setSelectedCourseId(courseId)
    try {
      setError(null)
      const data = await coursesApi.getDetail(courseId)
      setDetail(data)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('강의 상세 정보를 불러오는데 실패했습니다.')
      setError(error)
      console.error('Failed to load course detail:', err)
    }
  }

  const getBadgeClass = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return styles.badgeBeginner
      case 'intermediate':
        return styles.badgeIntermediate
      case 'advanced':
        return styles.badgeAdvanced
      default:
        return ''
    }
  }

  // 비율에 따른 색상 반환
  const getColorByPercent = (percent: number) => {
    if (percent >= 50) return { main: '#28a745', bg: 'rgba(40, 167, 69, 0.2)' } // 초록
    if (percent >= 20) return { main: '#ffc107', bg: 'rgba(255, 193, 7, 0.2)' } // 노랑
    return { main: '#dc3545', bg: 'rgba(220, 53, 69, 0.2)' } // 빨강
  }

  // 미니 도넛 차트 생성 함수
  const createMiniDoughnutData = (value: number, total: number) => {
    const percent = total > 0 ? (value / total) * 100 : 0
    const colors = getColorByPercent(percent)
    return {
      datasets: [{
        data: [value, total - value],
        backgroundColor: [colors.main, colors.bg],
        borderWidth: 0,
      }],
    }
  }

  const miniDoughnutOptions = {
    cutout: '70%',
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false },
    },
    responsive: true,
    maintainAspectRatio: true,
  }

  // 퍼널 최대값 (막대 너비 계산용)
  const funnelMax = detail?.funnel_data[0]?.count || 1

  if (loading) {
    return (
      <div className={styles.container}>
        <NavLinks variant="light" />
        <h1 className={styles.title}>📊 강의 상세 분석</h1>
        <Loading message="강의 데이터를 불러오는 중..." size="large" />
      </div>
    )
  }

  if (error && courses.length === 0) {
    return (
      <div className={styles.container}>
        <NavLinks variant="light" />
        <h1 className={styles.title}>📊 강의 상세 분석</h1>
        <ErrorMessage message={error.message} onRetry={loadCourses} />
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <NavLinks variant="light" />
      <h1 className={styles.title}>📊 강의 상세 분석</h1>

      <div className={styles.grid}>
        <div className={styles.card}>
          <h3 className={styles.cardTitle}>강의 목록</h3>
          <ul className={styles.courseList}>
            {courses.map((course) => (
              <li
                key={course.course_id}
                className={`${styles.courseItem} ${selectedCourseId === course.course_id ? styles.active : ''}`}
                onClick={() => selectCourse(course.course_id)}
              >
                <div className={styles.courseTitle}>{course.title}</div>
                <div className={styles.courseMeta}>
                  <span className={`${styles.badge} ${getBadgeClass(course.difficulty)}`}>
                    {course.difficulty}
                  </span>
                  <span>완강률 {course.completion_rate}%</span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.mainContent}>
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>📈 요약 통계</h3>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryItem}>
                <div className={styles.summaryValue}>
                  {detail?.enrollment_metrics.total_enrollments.toLocaleString() ?? '-'}
                </div>
                <div className={styles.summaryLabel}>총 수강신청</div>
                <div className={styles.miniDoughnut}>
                  {detail && (
                    <>
                      <Doughnut
                        data={createMiniDoughnutData(
                          detail.enrollment_metrics.total_enrollments,
                          detail.enrollment_metrics.total_enrollments
                        )}
                        options={miniDoughnutOptions}
                      />
                      <span className={styles.miniDoughnutLabel}>100%</span>
                    </>
                  )}
                </div>
              </div>
              <div className={styles.summaryItem}>
                <div className={styles.summaryValue}>
                  {detail?.enrollment_metrics.watched_at_least_once.toLocaleString() ?? '-'}
                </div>
                <div className={styles.summaryLabel}>1회 이상 시청</div>
                <div className={styles.miniDoughnut}>
                  {detail && (
                    <>
                      <Doughnut
                        data={createMiniDoughnutData(
                          detail.enrollment_metrics.watched_at_least_once,
                          detail.enrollment_metrics.total_enrollments
                        )}
                        options={miniDoughnutOptions}
                      />
                      <span className={styles.miniDoughnutLabel}>
                        {Math.round((detail.enrollment_metrics.watched_at_least_once / detail.enrollment_metrics.total_enrollments) * 100)}%
                      </span>
                    </>
                  )}
                </div>
              </div>
              <div className={styles.summaryItem}>
                <div className={styles.summaryValue}>
                  {detail?.progress_metrics.reached_50_percent.toLocaleString() ?? '-'}
                </div>
                <div className={styles.summaryLabel}>50% 진도 달성</div>
                <div className={styles.miniDoughnut}>
                  {detail && (
                    <>
                      <Doughnut
                        data={createMiniDoughnutData(
                          detail.progress_metrics.reached_50_percent,
                          detail.enrollment_metrics.total_enrollments
                        )}
                        options={miniDoughnutOptions}
                      />
                      <span className={styles.miniDoughnutLabel}>
                        {Math.round((detail.progress_metrics.reached_50_percent / detail.enrollment_metrics.total_enrollments) * 100)}%
                      </span>
                    </>
                  )}
                </div>
              </div>
              <div className={styles.summaryItem}>
                <div className={styles.summaryValue}>
                  {detail?.progress_metrics.completed.toLocaleString() ?? '-'}
                </div>
                <div className={styles.summaryLabel}>완강</div>
                <div className={styles.miniDoughnut}>
                  {detail && (
                    <>
                      <Doughnut
                        data={createMiniDoughnutData(
                          detail.progress_metrics.completed,
                          detail.enrollment_metrics.total_enrollments
                        )}
                        options={miniDoughnutOptions}
                      />
                      <span className={styles.miniDoughnutLabel}>
                        {Math.round((detail.progress_metrics.completed / detail.enrollment_metrics.total_enrollments) * 100)}%
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className={styles.card}>
            <h3 className={styles.cardTitle}>📈 수강 퍼널 (Course Funnel)</h3>
            <div className={styles.funnelContainer}>
              {detail ? (
                detail.funnel_data.map((step, index) => {
                  const widthPercent = (step.count / funnelMax) * 100
                  return (
                    <div key={index} className={styles.funnelStep}>
                      <div className={styles.funnelLabel}>{step.stage}</div>
                      <div className={styles.funnelBarWrapper}>
                        <div
                          className={styles.funnelBar}
                          style={{ '--bar-width': `${widthPercent}%` } as React.CSSProperties}
                        />
                        <span className={styles.funnelBarText}>
                          {step.count.toLocaleString()}명 ({step.rate}%)
                        </span>
                      </div>
                    </div>
                  )
                })
              ) : (
                <p>강의를 선택하세요</p>
              )}
            </div>
          </div>

          <div className={styles.card}>
            <h3 className={styles.cardTitle}>📊 평균 대비 비교</h3>
            {detail ? (
              <div className={styles.comparisonContainer}>
                <div className={styles.comparisonRow}>
                  <span className={styles.comparisonLabel}>완강률</span>
                  <div className={styles.comparisonBarContainer}>
                    <div className={styles.comparisonBarNegative}>
                      {detail.comparison_with_average.completion_rate.diff < 0 && (
                        <div
                          className={styles.comparisonBarFillNegative}
                          style={{ '--bar-width': `${Math.min(Math.abs(detail.comparison_with_average.completion_rate.diff) * 2, 100)}%` } as React.CSSProperties}
                        />
                      )}
                    </div>
                    <div className={styles.comparisonBarCenter}>
                      <span className={styles.comparisonValue}>{detail.comparison_with_average.completion_rate.value}%</span>
                    </div>
                    <div className={styles.comparisonBarPositive}>
                      {detail.comparison_with_average.completion_rate.diff > 0 && (
                        <div
                          className={styles.comparisonBarFillPositive}
                          style={{ '--bar-width': `${Math.min(detail.comparison_with_average.completion_rate.diff * 2, 100)}%` } as React.CSSProperties}
                        />
                      )}
                    </div>
                  </div>
                  <span className={`${styles.comparisonDiff} ${detail.comparison_with_average.completion_rate.is_above_average ? styles.diffPositive : styles.diffNegative}`}>
                    {detail.comparison_with_average.completion_rate.diff > 0 ? '+' : ''}{detail.comparison_with_average.completion_rate.diff}%
                  </span>
                </div>
                <div className={styles.comparisonRow}>
                  <span className={styles.comparisonLabel}>이탈률</span>
                  <div className={styles.comparisonBarContainer}>
                    <div className={styles.comparisonBarNegative}>
                      {detail.comparison_with_average.dropout_rate.diff < 0 && (
                        <div
                          className={styles.comparisonBarFillPositive}
                          style={{ '--bar-width': `${Math.min(Math.abs(detail.comparison_with_average.dropout_rate.diff) * 2, 100)}%` } as React.CSSProperties}
                        />
                      )}
                    </div>
                    <div className={styles.comparisonBarCenter}>
                      <span className={styles.comparisonValue}>{detail.comparison_with_average.dropout_rate.value}%</span>
                    </div>
                    <div className={styles.comparisonBarPositive}>
                      {detail.comparison_with_average.dropout_rate.diff > 0 && (
                        <div
                          className={styles.comparisonBarFillNegative}
                          style={{ '--bar-width': `${Math.min(detail.comparison_with_average.dropout_rate.diff * 2, 100)}%` } as React.CSSProperties}
                        />
                      )}
                    </div>
                  </div>
                  <span className={`${styles.comparisonDiff} ${!detail.comparison_with_average.dropout_rate.is_above_average ? styles.diffPositive : styles.diffNegative}`}>
                    {detail.comparison_with_average.dropout_rate.diff > 0 ? '+' : ''}{detail.comparison_with_average.dropout_rate.diff}%
                  </span>
                </div>
                <div className={styles.comparisonLegend}>
                  <span className={styles.comparisonLegendItem}><span className={styles.legendDotNegative}></span>평균 이하</span>
                  <span className={styles.comparisonLegendItem}><span className={styles.legendDotPositive}></span>평균 이상</span>
                </div>
              </div>
            ) : (
              <p>강의를 선택하세요</p>
            )}
          </div>

          <div className={styles.card}>
            <h3 className={styles.cardTitle}>⚠️ 이탈 지표</h3>
            {detail ? (
              <div className={styles.dropoutInfo}>
                <div className={styles.dropoutVisual}>
                  <div className={styles.dropoutMainStat}>
                    <div className={styles.dropoutStatCircle}>
                      <span className={styles.dropoutStatNumber}>{detail.dropout_metrics.total_dropouts.toLocaleString()}</span>
                      <span className={styles.dropoutStatUnit}>명</span>
                    </div>
                    <span className={styles.dropoutStatLabel}>총 이탈자</span>
                  </div>
                  <div className={styles.dropoutProgressSection}>
                    <div className={styles.dropoutProgressLabel}>평균 이탈 지점</div>
                    <div className={styles.dropoutProgressBar}>
                      <div className={styles.dropoutProgressTrack}>
                        <div
                          className={styles.dropoutProgressFill}
                          style={{ '--progress': `${detail.dropout_metrics.average_dropout_point}%` } as React.CSSProperties}
                        />
                        <div
                          className={styles.dropoutProgressMarker}
                          style={{ '--position': `${detail.dropout_metrics.average_dropout_point}%` } as React.CSSProperties}
                        >
                          <span className={styles.dropoutProgressValue}>{Math.round(detail.dropout_metrics.average_dropout_point)}%</span>
                        </div>
                      </div>
                      <div className={styles.dropoutProgressScale}>
                        <span>0%</span>
                        <span>50%</span>
                        <span>100%</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className={styles.dropoutPeakSection}>
                  <div className={styles.dropoutPeakBadge}>
                    <span className={styles.dropoutPeakIcon}>🚨</span>
                    <span className={styles.dropoutPeakText}>최다 이탈 구간</span>
                  </div>
                  <div className={styles.dropoutPeakValue}>
                    {detail.dropout_metrics.peak_dropout_segment}
                    <span className={styles.dropoutPeakRate}>({Math.round(detail.dropout_metrics.peak_dropout_rate)}%)</span>
                  </div>
                </div>
                <div className={styles.engagementStats}>
                  <div className={styles.engagementItem}>
                    <div className={styles.engagementIcon}>⏱️</div>
                    <div className={styles.engagementContent}>
                      <span className={styles.engagementValue}>{Math.round(detail.engagement_metrics.average_watch_time_minutes)}분</span>
                      <span className={styles.engagementLabel}>평균 시청 시간</span>
                    </div>
                  </div>
                  <div className={styles.engagementItem}>
                    <div className={styles.engagementIcon}>📅</div>
                    <div className={styles.engagementContent}>
                      <span className={styles.engagementValue}>{Math.round(detail.engagement_metrics.average_days_to_complete)}일</span>
                      <span className={styles.engagementLabel}>완강까지 평균</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <p>강의를 선택하세요</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CoursesPage
