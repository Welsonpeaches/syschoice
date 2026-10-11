import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useHardwareProbe } from '@/composables/useHardwareProbe'

describe('useHardwareProbe', () => {
  beforeEach(() => {
    // jsdom has no WebGL context, which is exactly the fallback path we want.
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
  })

  it('degrades to unknown instead of inventing values', () => {
    const { reading, detect } = useHardwareProbe()
    detect()
    expect(reading.value.source).toBe('auto')
    // jsdom exposes neither deviceMemory nor a WebGL renderer.
    expect(reading.value.memoryGB).toBeUndefined()
    expect(reading.value.gpu).toBeUndefined()
    expect(['number', 'undefined']).toContain(typeof reading.value.cores)
  })

  it('accepts manual overrides and clears them when emptied', () => {
    const { reading, override } = useHardwareProbe()
    override('memoryGB', '32')
    expect(reading.value.memoryGB).toBe(32)
    expect(reading.value.source).toBe('manual')

    override('memoryGB', '')
    expect(reading.value.memoryGB).toBeUndefined()

    override('gpu', 'RTX 4060')
    expect(reading.value.gpu).toBe('RTX 4060')
  })
})
