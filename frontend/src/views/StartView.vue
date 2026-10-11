<script setup lang="ts">
import { Cpu, MemoryStick, MonitorSmartphone, Play } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import type { CandidateSummary } from '@/api/types'
import SystemLogo from '@/components/SystemLogo.vue'
import { useHardwareProbe } from '@/composables/useHardwareProbe'
import { t } from '@/i18n'
import { useAssessmentStore } from '@/stores/assessment'

const router = useRouter()
const store = useAssessmentStore()
const { reading, probing, detect } = useHardwareProbe()
const hovered = ref<CandidateSummary | null>(null)

const candidates = computed(() => store.catalog?.candidates ?? [])
const preview = computed(() => hovered.value ?? candidates.value[0] ?? null)

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

// The four families are the shape of the whole answer space, so they get the
// first real colour on the page.
const families = [
  { label: 'Windows', count: 1, color: '#2E7CD6' },
  { label: 'macOS', count: 1, color: '#8A8A8E' },
  { label: 'Linux', count: 67, color: '#C4762A' },
  { label: 'BSD', count: 3, color: '#B03A48' },
]

const facts = [
  { value: '72', label: '候选系统' },
  { value: '28', label: '问卷题目' },
  { value: '9', label: '评估维度' },
]

onMounted(() => {
  detect()
  store.ensureLoaded()
})

function start() {
  store.begin()
  router.push({ name: 'hardware' })
}
</script>

<template>
  <div>
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

      <dl class="mt-10 grid grid-cols-3 gap-x-6 gap-y-4 border-t border-line pt-6">
        <div v-for="fact in facts" :key="fact.label">
          <dt class="mono-value text-[24px] font-medium">{{ fact.value }}</dt>
          <dd class="text-[12px] text-graphite">{{ fact.label }}</dd>
        </div>
      </dl>

      <div class="mt-8">
        <p class="text-[12px] text-graphite">候选范围</p>
        <div class="mt-2.5 flex h-2.5 gap-0.5 overflow-hidden rounded-full bg-paper-2">
          <span
            v-for="family in families"
            :key="family.label"
            class="h-full first:rounded-l-full last:rounded-r-full"
            :style="{ flexGrow: family.count, backgroundColor: family.color }"
            :title="`${family.label} ${family.count}`"
          />
        </div>
        <ul class="mt-3 flex flex-wrap gap-x-5 gap-y-1.5">
          <li v-for="family in families" :key="family.label" class="flex items-center gap-2">
            <span class="h-2.5 w-2.5 rounded-sm" :style="{ backgroundColor: family.color }" />
            <span class="text-[12px]">{{ family.label }}</span>
            <span class="mono-value text-[12px] text-graphite">{{ family.count }}</span>
          </li>
        </ul>
      </div>
    </div>

    <aside class="panel h-fit p-5">
      <div class="flex items-center justify-between">
        <h2 class="flex items-center gap-2 text-[13px] font-semibold">
          <span class="h-2 w-2 rounded-full bg-flux" />
          {{ t('start.detected') }}
        </h2>
        <button
          type="button"
          class="mono-value text-[11px] text-graphite underline decoration-dotted hover:text-ink"
          :disabled="probing"
          @click="detect"
        >
          {{ probing ? '…' : t('start.recheck') }}
        </button>
      </div>

      <ul class="mt-3">
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
            class="mono-value max-w-[62%] truncate rounded-sm text-right text-[12px]"
            :title="row.value"
          >
            {{ row.value }}
          </span>
        </li>
      </ul>

      <p class="mt-4 border-t border-line pt-3 text-[12px] leading-relaxed text-graphite">
        探测结果只在本机使用。读不到的项会按“未知”处理，不影响继续测试。
      </p>
    </aside>
  </section>

  <!-- The whole answer space, one tile per system: the page's visual anchor. -->
  <section v-if="candidates.length" class="mt-14 border-t border-line pt-8">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 class="text-[19px] font-semibold">会被比较的全部候选</h2>
        <p class="mt-1 text-[13px] text-graphite">
          每个方块是一个候选系统，按系统族着色。指针停在方块上可以看它是什么。
        </p>
      </div>
      <p class="mono-value text-[12px] text-graphite">{{ candidates.length }} 个</p>
    </div>

    <div class="mt-5 grid grid-cols-[repeat(auto-fill,42px)] gap-2">
      <button
        v-for="candidate in candidates"
        :key="candidate.id"
        type="button"
        class="group transition-transform duration-150 hover:z-10 hover:scale-[1.18]"
        :aria-label="candidate.name"
        @mouseenter="hovered = candidate"
        @focus="hovered = candidate"
        @click="hovered = candidate"
      >
        <SystemLogo
          :id="candidate.id"
          :color="candidate.color"
          :monogram="candidate.monogram"
          :size="42"
          :radius="7"
        />
      </button>
    </div>

    <div
      v-if="preview"
      class="panel mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 p-3"
      aria-live="polite"
    >
      <SystemLogo
        :id="preview.id"
        :color="preview.color"
        :monogram="preview.monogram"
        :size="34"
      />
      <span class="text-[15px] font-semibold">{{ preview.name }}</span>
      <span class="pill">{{ preview.group }}</span>
      <span v-if="preview.lineage" class="text-[12px] text-graphite">
        血统 {{ preview.lineage }}
      </span>
      <span class="w-full text-[12px] text-graphite">{{ preview.blurb }}</span>
    </div>
  </section>

  <section v-if="store.history.length" class="mt-12 border-t border-line pt-6">
    <h2 class="text-[13px] font-semibold">本机的历史结果</h2>
    <ul class="mt-3 flex flex-wrap gap-2">
      <li v-for="entry in store.history" :key="entry.shareCode">
        <RouterLink
          :to="{ name: 'result', params: { code: entry.shareCode } }"
          class="panel flex items-center gap-2.5 px-3 py-1.5 text-[12px] transition-transform hover:-translate-y-px"
        >
          <span>{{ entry.topName }}</span>
          <span class="mono-value text-flux">{{ entry.match }}%</span>
        </RouterLink>
      </li>
    </ul>
  </section>
  </div>
</template>
