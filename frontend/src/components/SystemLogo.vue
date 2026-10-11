<script setup lang="ts">
import { computed } from 'vue'

import { LOGOS } from '@/assets/logos'

const props = withDefaults(
  defineProps<{
    id: string
    color: string
    monogram?: string
    size?: number
    radius?: number
  }>(),
  { monogram: '', size: 36, radius: 7 },
)

const logo = computed(() => LOGOS[props.id])

/** Relative luminance decides whether the glyph should be white or ink. */
function readableOn(hex: string) {
  const clean = hex.replace('#', '')
  if (clean.length !== 6) return '#FFFFFF'
  const channel = (value: number) =>
    value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  const r = channel(parseInt(clean.slice(0, 2), 16) / 255)
  const g = channel(parseInt(clean.slice(2, 4), 16) / 255)
  const b = channel(parseInt(clean.slice(4, 6), 16) / 255)
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
  return luminance > 0.42 ? '#14181C' : '#FFFFFF'
}

const foreground = computed(() => readableOn(props.color))
const glyph = computed(() => Math.round(props.size * 0.58))
</script>

<template>
  <span
    class="monogram shrink-0"
    :style="{
      backgroundColor: color,
      color: foreground,
      width: `${size}px`,
      height: `${size}px`,
      borderRadius: `${radius}px`,
    }"
    :title="logo?.title ?? monogram"
  >
    <svg
      v-if="logo"
      :width="glyph"
      :height="glyph"
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
    >
      <path :d="logo.path" fill="currentColor" />
    </svg>
    <span
      v-else
      class="font-semibold leading-none"
      :style="{ fontSize: `${Math.round(size * 0.42)}px` }"
    >
      {{ monogram || '•' }}
    </span>
  </span>
</template>
