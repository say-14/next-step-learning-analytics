import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Card from './Card'

describe('Card 컴포넌트', () => {
  it('children이 렌더링되어야 한다', () => {
    render(<Card>카드 내용</Card>)
    expect(screen.getByText('카드 내용')).toBeInTheDocument()
  })

  it('title이 렌더링되어야 한다', () => {
    render(<Card title="카드 제목">내용</Card>)
    expect(screen.getByRole('heading', { name: '카드 제목' })).toBeInTheDocument()
  })

  it('title이 없으면 heading이 렌더링되지 않아야 한다', () => {
    render(<Card>내용만</Card>)
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })

  it('hoverable이 true일 때 hoverable 클래스가 적용되어야 한다', () => {
    const { container } = render(<Card hoverable>내용</Card>)
    const card = container.firstChild as HTMLElement
    expect(card?.className).toMatch(/hoverable/i)
  })

  it('padding에 따라 다른 클래스가 적용되어야 한다', () => {
    const { container, rerender } = render(<Card padding="small">내용</Card>)
    const card = container.firstChild as HTMLElement
    expect(card?.className).toMatch(/paddingSmall/i)

    rerender(<Card padding="medium">내용</Card>)
    expect(card?.className).toMatch(/paddingMedium/i)

    rerender(<Card padding="large">내용</Card>)
    expect(card?.className).toMatch(/paddingLarge/i)
  })
})
