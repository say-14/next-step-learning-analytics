import styles from './Loading.module.css'

interface LoadingProps {
  /** 로딩 메시지 */
  message?: string
  /** 로딩 크기 */
  size?: 'small' | 'medium' | 'large'
  /** 전체 화면 오버레이 여부 */
  fullScreen?: boolean
}

const Loading = ({
  message = '로딩 중...',
  size = 'medium',
  fullScreen = false
}: LoadingProps) => {
  const content = (
    <div className={`${styles.container} ${styles[size]}`}>
      <div className={styles.spinner}>
        <div className={styles.spinnerRing}></div>
        <div className={styles.spinnerRing}></div>
        <div className={styles.spinnerRing}></div>
      </div>
      {message && <p className={styles.message}>{message}</p>}
    </div>
  )

  if (fullScreen) {
    return <div className={styles.fullScreen}>{content}</div>
  }

  return content
}

export default Loading
