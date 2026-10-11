<script setup lang="ts">
import { Cpu, MemoryStick, MonitorSmartphone, Play } from 'lucide-vue-next'
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useHardwareProbe } from '@/composables/useHardwareProbe'
import { t } from '@/i18n'
import { useAssessmentStore } from '@/stores/assessment'

const router = useRouter()
const store = useAssessmentStore()
const { reading, probing, detect } = useHardwareProbe()

const readings = computed(() => [
  {
    icon: Cpu,
    label: 'CPU 逻辑核心',
    value: reading.value.cores ? String(reading.value.cores) : t('hardware.unknown'),
  },
  {
    icon: MemoryStick,
    label: '设备内存',
    value: reading.value.memoryGB ? `${reading.value.memoryGB} GB` : t('hardware.unknown'),
  },
  {
    icon: MonitorSmartphone,
    label: '图形渲染器',
    value: reading.value.gpu ?? t('hardware.unknown'),
    wide: true,
  },
  { label: '系统平台', value: reading.value.platform ?? t('hardware.unknown') },
  { label: '触控点数', value: String(reading.value.touchPoints ?? 0) },
])

const facts = [
  { value: '72', label: '候选系统' },
  { value: '4', label: '系统族' },
  { value: '28', label: '问卷题目' },
  { value: '9', label: '评估维度' },
]

onMounted(() => {
  detect()
})

function start() {
  store.begin()
  router.push({ name: 'hardware' })
}
</script>

<template>
  <section class="grid gap-10 py-4 md:grid-cols-[minmax(0,1fr)_360px] md:gap-14">
    <div class="flex flex-col justify-center">
      <h1 class="max-w-[16ch] text-[34px] font-semibold leading-[1.15] sm:text-[42px]">
        选出一个真正适合你的操作系统
      </h1>
      <p class="mt-5 max-w-[52ch] text-[15px] leading-relaxed text-graphite">
        先探测这台机器的硬件，再回答一组关于使用场景、软件依赖和技术习惯的问题，
        最后在 Windows、macOS、67 个 Linux 发行版与 3 个 BSD 之间得到一份带解释的排名。
      </p>

      <div class="mt-8 flex flex-wrap items-center gap-3">
        <button type="button" class="btn-primary" @click="start">
          <Play :size="16" />
          {{ t('start.cta') }}
        </button>
        <RouterLink to="/stats" class="btn-quiet">{{ t('nav.stats') }}</RouterLink>
      </div>

      <dl class="mt-10 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-line pt-6 sm:grid-cols-4">
        <div v-for="fact in facts" :key="fact.label">
          <dt class="mono-value text-[22px] font-medium">{{ fact.value }}</dt>
          <dd class="text-[12px] text-graphite">{{ fact.label }}</dd>
        </div>
      </dl>
    </div>

    <aside class="border border-line bg-white/60 p-5">
      <div class="flex items-center justify-between">
        <h2 class="text-[13px] font-semibold">{{ t('start.detected') }}</h2>
        <button
          type="button"
          class="mono-value text-[11px] text-graphite underline decoration-dotted hover:text-ink"
          :disabled="probing"
          @click="detect"
        >
          {{ t('start.recheck') }}
        </button>
      </div>

      <ul class="mt-4">
        <li
          v-for="row in readings"
          :key="row.label"
          class="flex items-baseline justify-between gap-4 border-t border-line py-2.5 first:border-t-0"
        >
          <span class="flex items-center gap-2 text-[12px] text-graphite">
            <component :is="row.icon" v-if="row.icon" :size="14" />
            {{ row.label }}
          </span>
          <span
            class="mono-value max-w-[62%] truncate text-right text-[12px]"
            :title="row.value"
          >
            {{ row.value }}
          </span>
        </li>
      </ul>

      <p class="mt-4 text-[12px] leading-relaxed text-graphite">
        探测结果只在本机使用。读不到的项会按“未知”处理，不影响继续测试。
      </p>
    </aside>
  </section>

  <section v-if="store.history.length" class="mt-12 border-t border-line pt-6">
    <h2 class="text-[13px] font-semibold">本机的历史结果</h2>
    <ul class="mt-3 flex flex-wrap gap-2">
      <li v-for="entry in store.history" :key="entry.shareCode">
        <RouterLink
          :to="{ name: 'result', params: { code: entry.shareCode } }"
          class="btn-quiet px-3 py-1.5 text-[12px]"
        >
          <span>{{ entry.topName }}</span>
          <span class="mono-value text-graphite">{{ entry.match }}%</span>
        </RouterLink>
      </li>
    </ul>
  </section>
</template>
