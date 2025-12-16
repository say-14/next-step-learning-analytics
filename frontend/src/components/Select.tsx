import { SelectHTMLAttributes, forwardRef } from 'react'
import styles from './Select.module.css'

interface SelectOption {
  value: string
  label: string
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** 라벨 */
  label?: string
  /** 옵션 목록 */
  options: SelectOption[]
  /** 에러 메시지 */
  error?: string
  /** 플레이스홀더 */
  placeholder?: string
  /** 전체 너비 */
  fullWidth?: boolean
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, error, placeholder, fullWidth = false, className = '', id, ...props }, ref) => {
    const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`

    const containerClasses = [
      styles.container,
      fullWidth ? styles.fullWidth : '',
    ]
      .filter(Boolean)
      .join(' ')

    const selectClasses = [
      styles.select,
      error ? styles.selectError : '',
      className,
    ]
      .filter(Boolean)
      .join(' ')

    return (
      <div className={containerClasses}>
        {label && (
          <label htmlFor={selectId} className={styles.label}>
            {label}
          </label>
        )}
        <div className={styles.selectWrapper}>
          <select
            ref={ref}
            id={selectId}
            className={selectClasses}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <span className={styles.arrow}>&#9662;</span>
        </div>
        {error && <span className={styles.error}>{error}</span>}
      </div>
    )
  }
)

Select.displayName = 'Select'

export default Select
