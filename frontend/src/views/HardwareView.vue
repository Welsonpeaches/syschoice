<script setup lang="ts">
import { ArrowRight, RefreshCw } from 'lucide-vue-next'
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import type { HardwareReading } from '@/api/types'
import { useHardwareProbe } from '@/composables/useHardwareProbe'
import { t } from '@/i18n'
import { useAssessmentStore } from '@/stores/assessment'

const router = useRouter()
const store = useAssessmentStore()
const { reading, probing, detect, override } = useHardwareProbe()

const rows = computed(() => [
  { label: 'CPU 逻辑核心', value: reading.value.cores ? String(reading.value.cores) : null },
  {
    label: '设备内存',
    value: reading.value.memoryGB ? `${reading.value.memoryGB} GB` : null,
  },
  { label: '图形渲染器', value: reading.value.gpu ?? null },
  { label: '系统平台', value: reading.value.platform ?? null },
  {
    label: '屏幕像素比',
    value: reading.value.devicePixelRatio ? String(reading.value.devicePixelRatio) : null,
  },
  { label: '触控点数', value: String(reading.value.touchPoints ?? 0) },
])

const memoryModel = computed({
  get: () => (reading.value.memoryGB ? String(reading.value.memoryGB) : ''),
  set: (value: string) => override('memoryGB', value),
})

const gpuModel = computed({
  get: () => reading.value.gpu ?? '',
  set: (value: string) => override('gpu', value),
})

onMounted(() => {
  detect()
})

function next() {
  store.setHardware(reading.value as HardwareReading)
  router.push({ name: 'interview' })
}

function skip() {
  store.setHardware({ source: 'skipped' })
  router.push({ name: 'interview' })
}
</script>

<template>
  <section data-view="hardware">
    <h1 class="text-[22px] font-semibold">{{ t('hardware.title') }}</h1>
    <p class="mt-2 max-w-[60ch] text-[14px] text-graphite">{{ t('hardware.desc') }}</p>

    <div class="panel mt-7 overflow-hidden">
      <ul>
        <li
          v-for="row in rows"
          :key="row.label"
          class="flex items-center justify-between gap-6 border-b border-line px-4 py-3 transition-colors last:border-b-0 hover:bg-surface-2"
        >
          <span class="text-[13px] text-graphite">{{ row.label }}</span>
          <span
            class="mono-value text-[13px]"
            :class="row.value ? 'text-ink' : 'text-line-strong'"
          >
            {{ row.value ?? t('hardware.unknown') }}
          </span>
        </li>
      </ul>
    </div>

    <div class="mt-5 grid gap-4 sm:grid-cols-2">
      <label class="block">
        <span class="text-[12px] text-graphite">手动填写内存（GB）</span>
        <input v-model="memoryModel" class="field-input mt-1.5" inputmode="numeric" placeholder="例如 16" />
      </label>
      <label class="block">
        <span class="text-[12px] text-graphite">手动填写显卡</span>
        <input v-model="gpuModel" class="field-input mt-1.5" placeholder="例如 RTX 4060 / 核显" />
      </label>
    </div>
    <p class="mt-2 text-[12px] text-graphite">{{ t('hardware.manualHint') }}</p>

    <div class="mt-8 flex flex-wrap items-center gap-3">
      <button type="button" class="btn-primary" @click="next">
        {{ t('common.next') }}
        <ArrowRight :size="16" />
      </button>
      <button type="button" class="btn-quiet" :disabled="probing" @click="detect">
        <RefreshCw :size="15" />
        {{ t('common.retry') }}
      </button>
      <button type="button" class="text-[13px] text-graphite underline decoration-dotted hover:text-ink" @click="skip">
        {{ t('common.skip') }}
      </button>
    </div>
  </section>
</template>
