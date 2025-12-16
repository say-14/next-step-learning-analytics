import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Loading from './Loading'

describe('Loading 컴포넌트', () => {
  it('기본 메시지가 렌더링되어야 한다', () => {
    render(<Loading />)
    expect(screen.getByText('로딩 중...')).toBeInTheDocument()
  })

  it('커스텀 메시지가 렌더링되어야 한다', () => {
    render(<Loading message="데이터를 불러오는 중..." />)
    expect(screen.getByText('데이터를 불러오는 중...')).toBeInTheDocument()
  })

  it('size에 따라 다른 클래스가 적용되어야 한다', () => {
    const { container, rerender } = render(<Loading size="small" />)
    const firstChild = container.firstChild as HTMLElement
    expect(firstChild?.className).toMatch(/small/i)

    rerender(<Loading size="medium" />)
    expect(firstChild?.className).toMatch(/medium/i)

    rerender(<Loading size="large" />)
    expect(firstChild?.className).toMatch(/large/i)
  })

  it('fullScreen이 true일 때 전체 화면 스타일이 적용되어야 한다', () => {
    const { container } = render(<Loading fullScreen />)
    const firstChild = container.firstChild as HTMLElement
    expect(firstChild?.className).toMatch(/fullScreen/i)
  })
})
