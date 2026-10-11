<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { Dimension } from '@/api/types'
import { echarts, type ECharts, type EChartsCoreOption } from '@/lib/echarts'

const props = defineProps<{
  labels: string[]
  values: number[]
  dimensions: Dimension[]
}>()

const host = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null
let observer: ResizeObserver | null = null

function labelFor(id: string) {
  const dimension = props.dimensions.find((item) => item.id === id)
  return dimension?.short ?? dimension?.label ?? id
}

function option(): EChartsCoreOption {
  return {
    animationDuration: 700,
    tooltip: { trigger: 'item' },
    radar: {
      // Kept tight so the longest axis name (创作与专业软件) never clips in the
      // narrow result column.
      center: ['50%', '52%'],
      radius: '60%',
      splitNumber: 4,
      axisName: {
        color: '#5A636B',
        fontSize: 12,
        fontFamily: 'IBM Plex Sans',
        overflow: 'break',
      },
      indicator: props.labels.map((id) => ({ name: labelFor(id), max: 100 })),
      splitLine: { lineStyle: { color: '#D3D7D2' } },
      splitArea: { areaStyle: { color: ['#F7F8F5', '#EFF1EE'] } },
      axisLine: { lineStyle: { color: '#D3D7D2' } },
    },
    series: [
      {
        type: 'radar',
        symbolSize: 5,
        lineStyle: { color: '#2F6B5E', width: 2 },
        itemStyle: { color: '#2F6B5E' },
        areaStyle: { color: 'rgba(47, 107, 94, 0.16)' },
        data: [{ value: props.values, name: '你的需求' }],
      },
    ],
  }
}

function render() {
  if (!host.value) return
  if (!chart) chart = echarts.init(host.value, undefined, { renderer: 'svg' })
  chart.setOption(option(), true)
}

onMounted(() => {
  render()
  if (host.value && typeof ResizeObserver !== 'undefined') {
    observer = new ResizeObserver(() => chart?.resize())
    observer.observe(host.value)
  }
})

watch(() => [props.labels, props.values], render, { deep: true })

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="host" class="h-[330px] w-full" role="img" aria-label="需求维度雷达图" />
</template>
