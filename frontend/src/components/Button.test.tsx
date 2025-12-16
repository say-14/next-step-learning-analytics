import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Button from './Button'

describe('Button 컴포넌트', () => {
  it('버튼 텍스트가 렌더링되어야 한다', () => {
    render(<Button>테스트 버튼</Button>)
    expect(screen.getByRole('button', { name: '테스트 버튼' })).toBeInTheDocument()
  })

  it('클릭 이벤트가 동작해야 한다', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>클릭</Button>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('disabled 상태에서는 클릭이 되지 않아야 한다', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick} disabled>비활성화</Button>)

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()

    fireEvent.click(button)
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('loading 상태에서는 비활성화되어야 한다', () => {
    render(<Button loading>로딩 중</Button>)

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })

  it('variant에 따라 다른 스타일이 적용되어야 한다', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>)
    expect(screen.getByRole('button').className).toMatch(/primary/i)

    rerender(<Button variant="secondary">Secondary</Button>)
    expect(screen.getByRole('button').className).toMatch(/secondary/i)

    rerender(<Button variant="danger">Danger</Button>)
    expect(screen.getByRole('button').className).toMatch(/danger/i)
  })

  it('size에 따라 다른 크기가 적용되어야 한다', () => {
    const { rerender } = render(<Button size="small">Small</Button>)
    expect(screen.getByRole('button').className).toMatch(/small/i)

    rerender(<Button size="medium">Medium</Button>)
    expect(screen.getByRole('button').className).toMatch(/medium/i)

    rerender(<Button size="large">Large</Button>)
    expect(screen.getByRole('button').className).toMatch(/large/i)
  })

  it('fullWidth가 true일 때 전체 너비 스타일이 적용되어야 한다', () => {
    render(<Button fullWidth>전체 너비</Button>)
    expect(screen.getByRole('button').className).toMatch(/fullWidth/i)
  })
})
