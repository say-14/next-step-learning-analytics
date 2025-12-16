import { Link } from 'react-router-dom'
import styles from './HomePage.module.css'

const HomePage = () => {
  const menuItems = [
    
    {
      path: '/level-test',
      icon: '🎯',
      title: '레벨 테스트',
      desc: '학력, 경험, 알고있는 개념을 기반으로 개발자 레벨을 추정합니다.',
      color: '#7c3aed',
    },
    {
      path: '/recommend',
      icon: '💡',
      title: '맞춤 추천',
      desc: '레벨과 희망 직무에 맞는 강의를 추천받습니다.',
      color: '#f59e0b',
    },
    {
      path: '/dropout',
      icon: '📉',
      title: '이탈 구간 분석',
      desc: '강의별 학습자 이탈 패턴을 분석하고 위험 구간을 파악합니다.',
      color: '#00d4ff',
    },
    {
      path: '/courses',
      icon: '📊',
      title: '강의 상세 분석',
      desc: '수강신청부터 완강까지 퍼널 분석과 상세 지표를 확인합니다.',
      color: '#10b981',
    },
    
  ]

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>NEXT STEP</h1>
      <p className={styles.subtitle}>Decide What to Learn Next</p>

      <div className={styles.menuGrid}>
        {menuItems.map((item) => (
          <Link key={item.path} to={item.path} className={styles.menuCard}>
            <div className={styles.menuIcon} style={{ color: item.color }}>
              {item.icon}
            </div>
            <div className={styles.menuTitle}>{item.title}</div>
            <div className={styles.menuDesc}>{item.desc}</div>
          </Link>
        ))}
      </div>

      <p className={styles.apiLink}>
        API 문서:{' '}
        <a href="/docs" target="_blank" rel="noopener noreferrer">
          /docs
        </a>{' '}
        |{' '}
        <a href="/redoc" target="_blank" rel="noopener noreferrer">
          /redoc
        </a>
      </p>
    </div>
  )
}

export default HomePage
