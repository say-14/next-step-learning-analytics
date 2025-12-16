import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useApi } from './useApi'

describe('useApi 훅', () => {
  it('초기 상태가 올바르게 설정되어야 한다', () => {
    const mockApiFunction = vi.fn()
    const { result } = renderHook(() => useApi(mockApiFunction))

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('execute 호출 시 loading이 true가 되어야 한다', async () => {
    const mockApiFunction = vi.fn(() => new Promise((resolve) => setTimeout(() => resolve({ data: 'test' }), 100)))
    const { result } = renderHook(() => useApi(mockApiFunction))

    act(() => {
      result.current.execute()
    })

    expect(result.current.loading).toBe(true)
  })

  it('성공적인 API 호출 후 data가 설정되어야 한다', async () => {
    const mockData = { id: 1, name: 'Test' }
    const mockApiFunction = vi.fn().mockResolvedValue(mockData)
    const { result } = renderHook(() => useApi(mockApiFunction))

    await act(async () => {
      await result.current.execute()
    })

    expect(result.current.data).toEqual(mockData)
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('API 호출 실패 시 error가 설정되어야 한다', async () => {
    const mockError = new Error('API 오류')
    const mockApiFunction = vi.fn().mockRejectedValue(mockError)
    const { result } = renderHook(() => useApi(mockApiFunction))

    await act(async () => {
      await result.current.execute()
    })

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toEqual(mockError)
  })

  it('reset 호출 시 상태가 초기화되어야 한다', async () => {
    const mockData = { id: 1, name: 'Test' }
    const mockApiFunction = vi.fn().mockResolvedValue(mockData)
    const { result } = renderHook(() => useApi(mockApiFunction))

    await act(async () => {
      await result.current.execute()
    })

    expect(result.current.data).toEqual(mockData)

    act(() => {
      result.current.reset()
    })

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('execute에 인자를 전달할 수 있어야 한다', async () => {
    const mockApiFunction = vi.fn().mockResolvedValue({ success: true })
    const { result } = renderHook(() => useApi(mockApiFunction))

    await act(async () => {
      await result.current.execute('arg1', 'arg2')
    })

    expect(mockApiFunction).toHaveBeenCalledWith('arg1', 'arg2')
  })
})
