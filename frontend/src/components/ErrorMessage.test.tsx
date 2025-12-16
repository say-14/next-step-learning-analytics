import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ErrorMessage from './ErrorMessage'

describe('ErrorMessage 컴포넌트', () => {
  it('기본 에러 메시지가 렌더링되어야 한다', () => {
    render(<ErrorMessage />)
    expect(screen.getByText('데이터를 불러오는 중 오류가 발생했습니다.')).toBeInTheDocument()
  })

  it('커스텀 에러 메시지가 렌더링되어야 한다', () => {
    render(<ErrorMessage message="서버 연결에 실패했습니다." />)
    expect(screen.getByText('서버 연결에 실패했습니다.')).toBeInTheDocument()
  })

  it('재시도 버튼이 동작해야 한다', () => {
    const handleRetry = vi.fn()
    render(<ErrorMessage onRetry={handleRetry} />)

    const retryButton = screen.getByRole('button', { name: '다시 시도' })
    fireEvent.click(retryButton)

    expect(handleRetry).toHaveBeenCalledTimes(1)
  })

  it('onRetry가 없으면 재시도 버튼이 렌더링되지 않아야 한다', () => {
    render(<ErrorMessage />)
    expect(screen.queryByRole('button', { name: '다시 시도' })).not.toBeInTheDocument()
  })

  it('compact 모드에서는 compact 클래스가 적용되어야 한다', () => {
    const { container } = render(<ErrorMessage compact />)
    const errorContainer = container.firstChild as HTMLElement
    expect(errorContainer?.className).toMatch(/compact/i)
  })
})
