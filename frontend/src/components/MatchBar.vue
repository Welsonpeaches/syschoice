<script setup lang="ts">
import { onMounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{ value: number; color?: string; animate?: boolean }>(),
  { color: 'var(--color-flux)', animate: true },
)

const width = ref(props.animate ? 0 : props.value)

onMounted(() => {
  if (!props.animate) return
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  if (reduced) {
    width.value = props.value
    return
  }
  // One deliberate reveal: the bar grows to its value on mount.
  requestAnimationFrame(() => {
    width.value = props.value
  })
})
</script>

<template>
  <div class="h-[6px] w-full bg-paper-2">
    <div
      class="h-full transition-[width] duration-700 ease-out"
      :style="{ width: `${width}%`, backgroundColor: color }"
    />
  </div>
</template>
