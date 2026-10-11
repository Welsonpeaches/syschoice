import { ref } from 'vue'

import type { HardwareReading } from '@/api/types'

/**
 * Best-effort hardware probe. Every field is optional: browsers expose
 * different subsets, and anything unavailable is simply left undefined so the
 * scorer can treat it as unknown rather than guessing.
 */
function readGpu(): string | undefined {
  try {
    const canvas = document.createElement('canvas')
    const gl = (canvas.getContext('webgl') ??
      canvas.getContext('experimental-webgl')) as WebGLRenderingContext | null
    if (!gl) return undefined
    const info = gl.getExtension('WEBGL_debug_renderer_info')
    if (!info) return undefined
    const renderer = gl.getParameter(info.UNMASKED_RENDERER_WEBGL)
    return typeof renderer === 'string' ? renderer : undefined
  } catch {
    return undefined
  }
}

function readPlatform(): string | undefined {
  const uaData = (navigator as Navigator & { userAgentData?: { platform?: string } }).userAgentData
  return uaData?.platform || navigator.platform || undefined
}

export function useHardwareProbe() {
  const reading = ref<HardwareReading>({})
  const probing = ref(false)

  function detect() {
    probing.value = true
    const next: HardwareReading = { source: 'auto' }

    const cores = navigator.hardwareConcurrency
    if (typeof cores === 'number' && cores > 0) next.cores = cores

    const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory
    if (typeof memory === 'number' && memory > 0) next.memoryGB = memory

    const gpu = readGpu()
    if (gpu) next.gpu = gpu

    const platform = readPlatform()
    if (platform) next.platform = platform

    if (typeof window !== 'undefined' && window.devicePixelRatio) {
      next.devicePixelRatio = Number(window.devicePixelRatio.toFixed(2))
    }

    if (typeof navigator.maxTouchPoints === 'number') {
      next.touchPoints = navigator.maxTouchPoints
    }

    reading.value = next
    probing.value = false
  }

  function override(field: 'memoryGB' | 'gpu', value: string) {
    const next = { ...reading.value, source: 'manual' }
    if (field === 'memoryGB') {
      const parsed = Number(value)
      if (value && Number.isFinite(parsed) && parsed > 0) next.memoryGB = parsed
      else delete next.memoryGB
    } else {
      if (value.trim()) next.gpu = value.trim()
      else delete next.gpu
    }
    reading.value = next
  }

  return { reading, probing, detect, override }
}
