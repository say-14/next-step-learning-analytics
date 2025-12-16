import { ReactNode } from 'react'
import styles from './Card.module.css'

interface CardProps {
  /** 카드 내용 */
  children: ReactNode
  /** 카드 제목 */
  title?: string
  /** 추가 CSS 클래스 */
  className?: string
  /** 패딩 크기 */
  padding?: 'none' | 'small' | 'medium' | 'large'
  /** 호버 효과 */
  hoverable?: boolean
}

const Card = ({
  children,
  title,
  className = '',
  padding = 'medium',
  hoverable = false,
}: CardProps) => {
  const cardClasses = [
    styles.card,
    styles[`padding${padding.charAt(0).toUpperCase() + padding.slice(1)}`],
    hoverable ? styles.hoverable : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={cardClasses}>
      {title && <h3 className={styles.title}>{title}</h3>}
      <div className={styles.content}>{children}</div>
    </div>
  )
}

export default Card
