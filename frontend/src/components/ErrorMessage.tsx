import styles from './ErrorMessage.module.css'

interface ErrorMessageProps {
  /** 에러 메시지 */
  message?: string
  /** 재시도 함수 */
  onRetry?: () => void
  /** 컴팩트 모드 (카드 내부용) */
  compact?: boolean
}

const ErrorMessage = ({
  message = '데이터를 불러오는 중 오류가 발생했습니다.',
  onRetry,
  compact = false
}: ErrorMessageProps) => {
  return (
    <div className={`${styles.container} ${compact ? styles.compact : ''}`}>
      <div className={styles.icon}>⚠️</div>
      <p className={styles.message}>{message}</p>
      {onRetry && (
        <button className={styles.retryButton} onClick={onRetry}>
          다시 시도
        </button>
      )}
    </div>
  )
}

export default ErrorMessage
