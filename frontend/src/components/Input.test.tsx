import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Input from './Input'

describe('Input 컴포넌트', () => {
  it('라벨이 렌더링되어야 한다', () => {
    render(<Input label="이메일" />)
    expect(screen.getByLabelText('이메일')).toBeInTheDocument()
  })

  it('placeholder가 표시되어야 한다', () => {
    render(<Input placeholder="이메일을 입력하세요" />)
    expect(screen.getByPlaceholderText('이메일을 입력하세요')).toBeInTheDocument()
  })

  it('입력 값이 변경되어야 한다', () => {
    const handleChange = vi.fn()
    render(<Input onChange={handleChange} />)

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'test@example.com' } })

    expect(handleChange).toHaveBeenCalled()
  })

  it('에러 메시지가 표시되어야 한다', () => {
    render(<Input error="이메일 형식이 올바르지 않습니다." />)
    expect(screen.getByText('이메일 형식이 올바르지 않습니다.')).toBeInTheDocument()
  })

  it('힌트 텍스트가 표시되어야 한다', () => {
    render(<Input hint="영문, 숫자 조합 8자 이상" />)
    expect(screen.getByText('영문, 숫자 조합 8자 이상')).toBeInTheDocument()
  })

  it('에러가 있으면 힌트 대신 에러가 표시되어야 한다', () => {
    render(<Input hint="힌트 텍스트" error="에러 메시지" />)
    expect(screen.queryByText('힌트 텍스트')).not.toBeInTheDocument()
    expect(screen.getByText('에러 메시지')).toBeInTheDocument()
  })

  it('fullWidth가 true일 때 전체 너비 스타일이 적용되어야 한다', () => {
    const { container } = render(<Input fullWidth />)
    const inputContainer = container.firstChild as HTMLElement
    expect(inputContainer?.className).toMatch(/fullWidth/i)
  })
})
