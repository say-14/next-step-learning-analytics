import { useState, useEffect, useRef } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line, Doughnut } from 'react-chartjs-2'
import NavLinks from '../components/NavLinks'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import { analysisApi } from '../services/api'
import type { Course, Summary, ChartData, DangerZone, DropoutReason } from '../types'
import styles from './DropoutPage.module.css'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler)

const DropoutPage = () => {
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [chartData, setChartData] = useState<ChartData | null>(null)
  const [dangerZones, setDangerZones] = useState<DangerZone[]>([])
  const [reasons, setReasons] = useState<DropoutReason[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const chartRef = useRef<ChartJS<'line'>>(null)

  useEffect(() => {
    loadCourses()
  }, [])

  const loadCourses = async () => {
    try {
      setError(null)
      const data = await analysisApi.getCourses()
      setCourses(data.courses)
      if (data.courses.length > 0) {
        selectCourse(data.courses[0].course_id)
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
      const [summaryData, chartDataRes, dangerZonesRes, reasonsRes] = await Promise.all([
        analysisApi.getSummary(courseId),
        analysisApi.getChartData(courseId),
        analysisApi.getDangerZones(courseId),
        analysisApi.getReasons(courseId),
      ])
      setSummary(summaryData)
      setChartData(chartDataRes)
      setDangerZones(dangerZonesRes.danger_zones)
      setReasons(reasonsRes.reasons)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('강의 데이터를 불러오는데 실패했습니다.')
      setError(error)
      console.error('Failed to load course data:', err)
    }
  }

  // chartData가 완전히 로드되었는지 확인
  // datasets[0].data = 이탈률(%), dropout_counts = 이탈자 수(명)
  const rawDropoutRates = chartData?.datasets?.[0]?.data ?? []
  const dropoutRates = rawDropoutRates.map((rate) => Math.round(rate))
  const isChartDataReady = chartData?.labels?.length && dropoutRates.length
  const maxDropoutRate = isChartDataReady ? Math.max(...dropoutRates) : 1

  // 라벨을 간단하게 변환 (0-10% → 0%, 10-20% → 10%, ...)
  const simpleLabels = chartData?.labels?.map((label) => {
    const match = label.match(/^(\d+)/)
    return match ? `${match[1]}%` : label
  }) ?? []

  // Area Chart 옵션
  const getAreaChartOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        padding: 12,
        displayColors: false,
        callbacks: {
          title: (context: { label: string }[]) => `📍 ${context[0].label} 구간`,
          label: (context: { parsed: { y: number }; dataIndex: number }) => {
            const dropoutCount = chartData?.dropout_counts?.[context.dataIndex] ?? 0
            return [`이탈률: ${Math.round(context.parsed.y)}%`, `이탈자: ${dropoutCount}명`]
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(255,255,255,0.1)' },
        ticks: { color: '#aaa', font: { size: 11 } },
        title: { display: true, text: '강의 진행률', color: '#888', font: { size: 12 } },
      },
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(255,255,255,0.1)' },
        ticks: { color: '#aaa', callback: (value: number) => `${Math.round(value)}%` },
        title: { display: true, text: '이탈률 (%)', color: '#888', font: { size: 12 } },
      },
    },
    elements: {
      line: { tension: 0.4 },
      point: { radius: 6, hoverRadius: 10, hitRadius: 10 },
    },
    interaction: { intersect: false, mode: 'index' as const },
  })

  // Area Chart 데이터
  const getAreaChartData = () => {
    if (!isChartDataReady) return { labels: [], datasets: [] }

    // 이탈률 기반 그라데이션 색상
    const ctx = chartRef.current?.ctx
    let gradient
    if (ctx) {
      gradient = ctx.createLinearGradient(0, 0, 0, 300)
      gradient.addColorStop(0, 'rgba(220, 53, 69, 0.6)')
      gradient.addColorStop(0.5, 'rgba(255, 193, 7, 0.4)')
      gradient.addColorStop(1, 'rgba(40, 167, 69, 0.1)')
    }

    return {
      labels: simpleLabels,
      datasets: [
        {
          label: '이탈률',
          data: dropoutRates,
          fill: true,
          backgroundColor: gradient || 'rgba(220, 53, 69, 0.3)',
          borderColor: '#dc3545',
          borderWidth: 3,
          pointBackgroundColor: dropoutRates.map((rate: number) => {
            const normalized = rate / maxDropoutRate
            if (normalized < 0.3) return '#28a745'
            if (normalized < 0.6) return '#ffc107'
            if (normalized < 0.8) return '#fd7e14'
            return '#dc3545'
          }),
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        },
      ],
    }
  }

  // 도넛 차트 색상
  const doughnutColors = ['#E8F1FA', '#C6DBEF', '#9ECAE1', '#6BAED6', '#3182BD', '#08519C']
  const doughnutColorClasses = [
    styles.doughnutColor1,
    styles.doughnutColor2,
    styles.doughnutColor3,
    styles.doughnutColor4,
    styles.doughnutColor5,
    styles.doughnutColor6,
  ]

  // 이탈 사유 총합 계산 및 백분율 추가
  const totalReasonCount = reasons.reduce((sum, r) => sum + r.count, 0)
  const reasonsWithPercentage = reasons.map((r) => ({
    ...r,
    percentage: totalReasonCount > 0 ? (r.count / totalReasonCount) * 100 : 0,
  }))

  // 도넛 차트 데이터
  const getDoughnutData = () => {
    const topReasons = reasonsWithPercentage.slice(0, 6)
    return {
      labels: topReasons.map((r) => r.reason),
      datasets: [
        {
          data: topReasons.map((r) => r.count),
          backgroundColor: doughnutColors,
          borderColor: '#1a1a2e',
          borderWidth: 0,
        },
      ],
    }
  }

  // 도넛 차트 옵션
  const getDoughnutOptions = () => ({
    responsive: true,
    maintainAspectRatio: false,
    cutout: '45%',

    // 캔버스 내부 여백 확보 (hover/툴팁 여유)
    layout: {
      padding: 5,
    },

    // hover로 튀어나오는 정도 최소화 (기본값/커스텀값 때문에 잘림 방지)
    hoverOffset: 5,

    // arc 테두리/hover 테두리 때문에 잘리는 경우 방지
    elements: {
      arc: {
        borderWidth: 0,
        hoverBorderWidth: 0,
      },
    },

    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        padding: 5,
        callbacks: {
          label: (context: { label: string; parsed: number; dataIndex: number }) => {
            const percentage = reasonsWithPercentage[context.dataIndex]?.percentage ?? 0
            return `${context.label}: ${context.parsed}명 (${Math.round(percentage)}%)`;
          },
        },
      },
    },
  })

  if (loading) {
    return (
      <div className={styles.container}>
        <NavLinks variant="light" />
        <h1 className={styles.title}>📊 학습 이탈 구간 분석</h1>
        <Loading message="데이터를 불러오는 중..." size="large" />
      </div>
    )
  }

  if (error && courses.length === 0) {
    return (
      <div className={styles.container}>
        <NavLinks variant="light" />
        <h1 className={styles.title}>📊 학습 이탈 구간 분석</h1>
        <ErrorMessage message={error.message} onRetry={loadCourses} />
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <NavLinks variant="light" />
      <h1 className={styles.title}>📊 학습 이탈 구간 분석</h1>

      <div className={styles.dashboard}>
        <aside className={styles.sidebar}>
          <h2 className={styles.sidebarTitle}>📚 강의 목록</h2>
          <ul className={styles.courseList}>
            {courses.map((course) => (
              <li
                key={course.course_id}
                className={`${styles.courseItem} ${selectedCourseId === course.course_id ? styles.active : ''}`}
                onClick={() => selectCourse(course.course_id)}
              >
                <div className={styles.courseTitle}>{course.title}</div>
                <div className={styles.courseStats}>
                  <span className={styles.statGood}>완강 {Math.round(course.completion_rate)}%</span>
                  <span className={styles.statBad}>이탈 {Math.round(course.dropout_rate)}%</span>
                </div>
              </li>
            ))}
          </ul>
        </aside>

        <main className={styles.mainContent}>
          <div className={styles.card}>
            <h3 className={styles.cardTitle}>📈 요약 통계</h3>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryItem}>
                <div className={styles.summaryValue}>{summary?.total_enrollments ?? '-'}</div>
                <div className={styles.summaryLabel}>총 수강생</div>
              </div>
              <div className={styles.summaryItem}>
                <div className={`${styles.summaryValue} ${styles.statBad}`}>
                  {summary ? `${Math.round(summary.overall_dropout_rate)}%` : '-'}
                </div>
                <div className={styles.summaryLabel}>이탈률</div>
                {summary && (
                  <div className={styles.miniProgressBarBad}>
                    <div
                      className={styles.miniProgressFillBad}
                      style={{ '--progress': `${summary.overall_dropout_rate}%` } as React.CSSProperties}
                    />
                  </div>
                )}
              </div>
              <div className={styles.summaryItem}>
                <div className={`${styles.summaryValue} ${styles.statGood}`}>
                  {summary ? `${Math.round(summary.completion_rate)}%` : '-'}
                </div>
                <div className={styles.summaryLabel}>완강률</div>
                {summary && (
                  <div className={styles.miniProgressBarGood}>
                    <div
                      className={styles.miniProgressFillGood}
                      style={{ '--progress': `${summary.completion_rate}%` } as React.CSSProperties}
                    />
                  </div>
                )}
              </div>
              <div className={styles.summaryItem}>
                <div className={styles.summaryValue}>
                  {summary ? `${Math.round(summary.average_dropout_point)}%` : '-'}
                </div>
                <div className={styles.summaryLabel}>평균 이탈 지점</div>
                {summary && (
                  <div className={styles.miniProgressBar}>
                    <div
                      className={styles.miniProgressFill}
                      style={{ '--progress': `${summary.average_dropout_point}%` } as React.CSSProperties}
                    />
                    <div
                      className={styles.miniProgressMarker}
                      style={{ '--position': `${summary.average_dropout_point}%` } as React.CSSProperties}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className={styles.card}>
            <h3 className={styles.cardTitle}>📊 구간별 이탈 분포</h3>
            <div className={styles.areaChartContainer}>
              {/* 포물선 영역 차트 */}
              <div className={styles.chartWrapper}>
                <Line
                  ref={chartRef}
                  data={getAreaChartData()}
                  options={getAreaChartOptions() as never}
                />
              </div>

              {/* 범례 */}
              <div className={styles.chartLegend}>
                <div className={styles.legendItem}>
                  <span className={styles.legendDot} style={{ backgroundColor: '#28a745' }} />
                  <span>낮은 이탈</span>
                </div>
                <div className={styles.legendItem}>
                  <span className={styles.legendDot} style={{ backgroundColor: '#ffc107' }} />
                  <span>보통</span>
                </div>
                <div className={styles.legendItem}>
                  <span className={styles.legendDot} style={{ backgroundColor: '#fd7e14' }} />
                  <span>주의</span>
                </div>
                <div className={styles.legendItem}>
                  <span className={styles.legendDot} style={{ backgroundColor: '#dc3545' }} />
                  <span>높은 이탈</span>
                </div>
              </div>

              {/* 피크 구간 표시 */}
              {isChartDataReady && (
                <div className={styles.peakInfo}>
                  <span className={styles.peakLabel}>최고 이탈 구간:</span>
                  <span className={styles.peakValue}>
                    {simpleLabels[dropoutRates.indexOf(maxDropoutRate)]} ({maxDropoutRate}%)
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className={styles.card}>
            <h3 className={styles.cardTitle}>⚠️ 위험 구간 (개선 필요)</h3>
            {dangerZones.length === 0 ? (
              <p className={styles.noData}>✅ 심각한 위험 구간이 없습니다!</p>
            ) : (
              <div className={styles.dangerBarChart}>
                {dangerZones.map((zone, index) => {
                  const maxRate = Math.max(...dangerZones.map((z) => z.dropout_rate))
                  const barWidth = (zone.dropout_rate / maxRate) * 100
                  const barColor =
                    zone.risk_level === 'critical'
                      ? '#dc3545'
                      : zone.risk_level === 'high'
                        ? '#fd7e14'
                        : '#ffc107'

                  return (
                    <div
                      key={index}
                      className={styles.dangerBarItem}
                      title={`💡 ${zone.recommendation}`}
                    >
                      <span className={styles.dangerBarLabel}>{zone.segment}</span>
                      <div className={styles.dangerBarTrack}>
                        <div
                          className={styles.dangerBarFill}
                          style={{ width: `${barWidth}%`, backgroundColor: barColor }}
                        />
                      </div>
                      <span className={styles.dangerBarValue} style={{ color: barColor }}>
                        {Math.round(zone.dropout_rate)}%
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div className={styles.card}>
            <h3 className={styles.cardTitle}>📝 주요 이탈 사유</h3>
            <div className={styles.doughnutContainer}>
              <div className={styles.doughnutChartWrap}>
                <div className={styles.doughnutChart}>
                  {reasons.length > 0 && (
                    <Doughnut data={getDoughnutData()} options={getDoughnutOptions() as never} />
                  )}
                </div>
              </div>
              <div className={styles.doughnutLegend}>
                {reasonsWithPercentage.slice(0, 6).map((reason, index) => (
                  <div
                    key={index}
                    className={styles.doughnutLegendItem}
                    title={`${reason.count}명`}
                  >
                    <span
                      className={`${styles.doughnutLegendColor} ${doughnutColorClasses[index]}`}
                    />
                    <span className={styles.doughnutLegendText}>
                      {reason.reason} ({Math.round(reason.percentage)}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default DropoutPage
