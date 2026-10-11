<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { api } from '@/api/client'
import type { StatsResponse } from '@/api/types'
import { t } from '@/i18n'
import { echarts, type ECharts, type EChartsCoreOption } from '@/lib/echarts'

const stats = ref<StatsResponse | null>(null)
const error = ref<string | null>(null)
const loading = ref(true)
const chartHost = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null

const summary = computed(() => {
  const data = stats.value
  if (!data) return []
  return [
    { value: String(data.total), label: t('stats.total') },
    { value: `${data.averageMatch}%`, label: t('stats.average') },
    { value: String(data.familyCount), label: t('stats.families') },
  ]
})

const familyRows = computed(() => {
  const data = stats.value
  if (!data || !data.total) return []
  return data.byFamily.map((row) => ({
    ...row,
    label: data.familyLabels[row.family] ?? row.family,
    color: data.familyColors[row.family] ?? '#5A636B',
    share: Math.round((row.count / data.total) * 100),
  }))
})

const maxTopCount = computed(() =>
  Math.max(1, ...(stats.value?.topCandidates ?? []).map((item) => item.count)),
)

function renderChart() {
  const data = stats.value
  if (!chartHost.value || !data) return
  if (!chart) chart = echarts.init(chartHost.value, undefined, { renderer: 'svg' })
  const option: EChartsCoreOption = {
    animationDuration: 600,
    grid: { left: 28, right: 12, top: 12, bottom: 24 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: data.daily.map((item) => item.date.slice(5)),
      axisLine: { lineStyle: { color: '#D3D7D2' } },
      axisLabel: { color: '#5A636B', fontSize: 11 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      // With only a day or two of data a line would be invisible; bars always read.
      min: 0,
      splitLine: { lineStyle: { color: '#E7E9E3' } },
      axisLabel: { color: '#5A636B', fontSize: 11 },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 22,
        data: data.daily.map((item) => item.count),
        itemStyle: { color: '#2F6B5E' },
      },
    ],
  }
  chart.setOption(option)
}

onMounted(async () => {
  try {
    stats.value = await api.stats()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
  await nextTick()
  renderChart()
})

watch(stats, renderChart)

onBeforeUnmount(() => {
  chart?.dispose()
  chart = null
})
</script>

<template>
  <section>
    <h1 class="text-[22px] font-semibold">{{ t('stats.title') }}</h1>

    <div v-if="loading" class="mt-6 flex items-center gap-2 text-graphite">
      <Loader2 :size="16" class="animate-spin" />
      {{ t('common.loading') }}
    </div>

    <p v-else-if="error" class="mt-6 border border-alert bg-alert-soft px-4 py-3 text-[13px] text-alert">
      {{ error }}
    </p>

    <template v-else-if="stats">
      <dl class="mt-6 grid gap-6 border-y border-line py-6 sm:grid-cols-3">
        <div v-for="item in summary" :key="item.label">
          <dt class="mono-value text-[28px] font-medium">{{ item.value }}</dt>
          <dd class="text-[12px] text-graphite">{{ item.label }}</dd>
        </div>
      </dl>

      <div v-if="!stats.total" class="mt-6 text-[13px] text-graphite">
        {{ t('common.empty') }}
      </div>

      <div v-else class="mt-8 grid gap-10 lg:grid-cols-2">
        <div>
          <h2 class="text-[13px] font-semibold">{{ t('stats.byFamily') }}</h2>
          <ul class="mt-3">
            <li v-for="row in familyRows" :key="row.family" class="border-t border-line py-3">
              <div class="flex items-baseline justify-between gap-3">
                <span class="text-[13px]">{{ row.label }}</span>
                <span class="mono-value text-[12px] text-graphite">
                  {{ row.count }} · {{ row.share }}%
                </span>
              </div>
              <div class="mt-2 h-[6px] w-full bg-paper-2">
                <div class="h-full" :style="{ width: `${row.share}%`, backgroundColor: row.color }" />
              </div>
            </li>
          </ul>
        </div>

        <div>
          <h2 class="text-[13px] font-semibold">{{ t('stats.topCandidates') }}</h2>
          <ul class="mt-3">
            <li
              v-for="item in stats.topCandidates"
              :key="item.id"
              class="flex items-center gap-3 border-t border-line py-2.5"
            >
              <span class="min-w-0 flex-1 truncate text-[13px]">{{ item.name }}</span>
              <span class="mono-value hidden shrink-0 text-[11px] text-graphite sm:inline">
                {{ stats.familyLabels[item.family] ?? item.family }}
              </span>
              <span class="h-[6px] w-20 shrink-0 bg-paper-2">
                <span
                  class="block h-full bg-flux"
                  :style="{ width: `${(item.count / maxTopCount) * 100}%` }"
                />
              </span>
              <span class="mono-value w-8 shrink-0 text-right text-[12px]">{{ item.count }}</span>
            </li>
          </ul>
        </div>

        <div class="lg:col-span-2">
          <h2 class="text-[13px] font-semibold">{{ t('stats.daily') }}</h2>
          <div ref="chartHost" class="mt-3 h-[220px] w-full" />
        </div>
      </div>
    </template>
  </section>
</template>
