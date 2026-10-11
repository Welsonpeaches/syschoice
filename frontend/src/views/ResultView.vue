<script setup lang="ts">
import { ChevronDown, Copy, Loader2, RotateCcw } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import type { CandidateEntry } from '@/api/types'
import MatchBar from '@/components/MatchBar.vue'
import RadarChart from '@/components/RadarChart.vue'
import ResultExtras from '@/components/ResultExtras.vue'
import SystemLogo from '@/components/SystemLogo.vue'
import { t } from '@/i18n'
import { useAssessmentStore } from '@/stores/assessment'

const props = defineProps<{ code: string }>()
const router = useRouter()
const store = useAssessmentStore()
const expanded = ref(false)
const copied = ref(false)

onMounted(async () => {
  await store.ensureLoaded()
  if (store.result?.shareCode !== props.code) await store.loadResult(props.code)
})

watch(
  () => props.code,
  async (code) => {
    if (store.result?.shareCode !== code) await store.loadResult(code)
  },
)

const result = computed(() => store.result)
const dimensions = computed(() => store.catalog?.dimensions ?? [])
const champion = computed(() => result.value?.top[0] ?? null)

const dimensionRows = computed(() => {
  const data = result.value
  if (!data) return []
  return data.radar.labels
    .map((id) => ({
      id,
      label: dimensions.value.find((dimension) => dimension.id === id)?.label ?? id,
      value: data.profile.dims[id] ?? 0,
      weight: data.profile.weights[id] ?? 0,
    }))
    .sort((a, b) => b.weight - a.weight)
})

const groupedFull = computed(() => {
  const data = result.value
  if (!data) return []
  const order = store.catalog?.groups ?? []
  const buckets = new Map<string, CandidateEntry[]>()
  for (const entry of data.full) {
    if (!buckets.has(entry.group)) buckets.set(entry.group, [])
    buckets.get(entry.group)!.push(entry)
  }
  return [...buckets.entries()]
    .sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0]))
    .map(([group, entries]) => ({ group, entries }))
})

const maxFamilyAverage = computed(() =>
  Math.max(1, ...(result.value?.families ?? []).map((item) => item.average)),
)

async function copyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    copied.value = true
    window.setTimeout(() => (copied.value = false), 2000)
  } catch {
    copied.value = false
  }
}

function restart() {
  store.reset()
  router.push({ name: 'hardware' })
}
</script>

<template>
  <div v-if="store.loading && !result" class="flex items-center gap-2 py-16 text-graphite">
    <Loader2 :size="16" class="animate-spin" />
    {{ t('common.loading') }}
  </div>

  <div
    v-else-if="!result"
    class="border border-alert bg-alert-soft px-5 py-4 text-[13px] text-alert"
  >
    {{ store.error ?? '没有找到这份结果。' }}
  </div>

  <div v-else>
    <!-- The verdict is the loudest thing on the page; everything else stays quiet. -->
    <section v-if="champion" class="band overflow-hidden">
      <div class="h-1.5 w-full" :style="{ backgroundColor: champion.color }" />
      <div class="p-6 sm:p-7">
        <p class="mono-value text-[11px] tracking-normal text-graphite">{{ t('result.title') }}</p>
        <div class="mt-4 flex flex-wrap items-center gap-x-5 gap-y-4">
          <SystemLogo
            :id="champion.id"
            :color="champion.color"
            :monogram="champion.monogram"
            :size="56"
            :radius="10"
          />
          <div class="min-w-0">
            <h1 class="text-[32px] font-semibold leading-tight sm:text-[40px]">
              {{ champion.name }}
            </h1>
            <p class="mt-1.5 flex flex-wrap items-center gap-2 text-[12px] text-graphite">
              <span class="pill">{{ champion.familyLabel }}</span>
              <span class="pill">{{ champion.group }}</span>
              <span v-if="champion.lineage" class="pill">血统 {{ champion.lineage }}</span>
            </p>
          </div>
          <div class="ml-auto text-right">
            <p class="mono-value text-[38px] font-medium leading-none text-flux">
              {{ champion.match }}<span class="text-[20px]">%</span>
            </p>
            <p class="mt-1 text-[11px] text-graphite">综合匹配度</p>
          </div>
        </div>
        <p class="mt-5 max-w-[62ch] text-[15px] leading-relaxed">{{ champion.blurb }}</p>

        <div
          v-if="result.evidenceNotes?.length"
          class="mt-4 rounded-card border border-flux bg-flux-soft p-3"
        >
          <p class="text-[12px] font-semibold text-flux-deep">
            {{ t('result.interviewUsed') }}
          </p>
          <ul class="mt-1.5 space-y-1">
            <li
              v-for="note in result.evidenceNotes"
              :key="note"
              class="flex gap-2 text-[12px] text-flux-deep"
            >
              <span class="mt-[7px] h-[5px] w-[5px] shrink-0 rounded-full bg-flux" />
              {{ note }}
            </li>
          </ul>
        </div>

        <div class="mt-6 flex flex-wrap gap-3">
          <button type="button" class="btn-primary" @click="copyLink">
            <Copy :size="15" />
            {{ copied ? t('result.copied') : t('result.share') }}
          </button>
          <button type="button" class="btn-quiet" @click="restart">
            <RotateCcw :size="15" />
            {{ t('result.restart') }}
          </button>
        </div>
      </div>
    </section>

    <section class="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div>
        <h2 class="text-[13px] font-semibold">{{ t('result.top') }}</h2>
        <ol class="mt-3 space-y-3">
          <li
            v-for="entry in result.top"
            :key="entry.id"
            class="panel p-4 transition-shadow duration-150 hover:shadow-lift sm:p-5"
            :class="entry.rank === 1 ? 'ring-1 ring-flux/25' : ''"
          >
            <div class="flex items-start gap-4">
              <span
                class="mono-value flex h-7 w-7 shrink-0 items-center justify-center rounded-card text-[13px] font-semibold text-white"
                :style="{ backgroundColor: entry.familyColor }"
              >
                {{ entry.rank }}
              </span>
              <SystemLogo
                :id="entry.id"
                :color="entry.color"
                :monogram="entry.monogram"
                :size="40"
              />
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-baseline justify-between gap-x-4">
                  <h3 class="text-[17px] font-semibold">{{ entry.name }}</h3>
                  <span class="mono-value text-[15px]">{{ entry.match }}%</span>
                </div>
                <p class="mt-0.5 text-[12px] text-graphite">
                  {{ entry.familyLabel }} · {{ entry.group }}
                  <template v-if="entry.lineage"> · 血统 {{ entry.lineage }}</template>
                </p>
                <div class="mt-3"><MatchBar :value="entry.match" :color="entry.color" /></div>
                <p class="mt-3 text-[13px] leading-relaxed text-graphite">{{ entry.blurb }}</p>

                <div
                  v-if="entry.notes.length"
                  class="mt-4 rounded-card border border-line bg-surface-2/70 p-3"
                >
                  <h4 class="text-[12px] font-semibold">{{ t('result.why') }}</h4>
                  <ul class="mt-2 space-y-1.5">
                    <li
                      v-for="(note, index) in entry.notes"
                      :key="index"
                      class="flex gap-2.5 text-[13px] leading-relaxed"
                    >
                      <span
                        class="mt-[7px] h-[6px] w-[6px] shrink-0"
                        :class="note.type === 'match' ? 'bg-flux' : 'bg-alert'"
                      />
                      <span :class="note.type === 'match' ? 'text-ink' : 'text-alert'">
                        {{ note.text }}
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </li>
        </ol>
      </div>

      <aside class="space-y-6">
        <div class="panel p-4">
          <h2 class="text-[13px] font-semibold">{{ t('result.radar') }}</h2>
          <RadarChart
            class="mt-2"
            :labels="result.radar.labels"
            :values="result.radar.values"
            :dimensions="dimensions"
          />
          <ul class="mt-2">
            <li
              v-for="row in dimensionRows"
              :key="row.id"
              class="flex items-center justify-between gap-4 border-t border-line py-1.5 first:border-t-0"
            >
              <span class="text-[12px]" :class="row.weight > 0.12 ? 'text-ink' : 'text-mist'">
                {{ row.label }}
              </span>
              <span class="flex items-center gap-2.5">
                <span class="h-[5px] w-16 overflow-hidden rounded-full bg-paper-2">
                  <span
                    class="block h-full rounded-full bg-flux"
                    :style="{ width: `${row.value}%` }"
                  />
                </span>
                <span class="mono-value w-8 text-right text-[12px] text-graphite">
                  {{ row.value }}
                </span>
              </span>
            </li>
          </ul>
        </div>

        <div class="panel p-4">
          <h2 class="text-[13px] font-semibold">{{ t('result.families') }}</h2>
          <ul class="mt-3">
            <li v-for="item in result.families" :key="item.family" class="py-2.5">
              <div class="flex items-baseline justify-between gap-3">
                <span class="flex items-center gap-2 text-[13px]">
                  <span class="h-2.5 w-2.5 rounded-sm" :style="{ backgroundColor: item.color }" />
                  {{ item.label }}
                </span>
                <span class="mono-value text-[12px] text-graphite">{{ item.average }}</span>
              </div>
              <div class="mt-2 h-[5px] w-full overflow-hidden rounded-full bg-paper-2">
                <div
                  class="h-full rounded-full"
                  :style="{
                    width: `${(item.average / maxFamilyAverage) * 100}%`,
                    backgroundColor: item.color,
                  }"
                />
              </div>
              <p v-if="item.best" class="mt-1.5 text-[11px] text-graphite">
                最佳：{{ item.best.name }} · {{ item.best.match }}%
              </p>
            </li>
          </ul>
        </div>
      </aside>
    </section>

    <section class="mt-10">
      <button
        type="button"
        class="btn-quiet w-full justify-between text-[13px]"
        @click="expanded = !expanded"
      >
        <span>
          {{ expanded ? t('result.collapse') : t('result.expand', { n: result.full.length }) }}
        </span>
        <ChevronDown
          :size="16"
          class="transition-transform duration-200"
          :class="expanded ? 'rotate-180' : ''"
        />
      </button>

      <div v-if="expanded" class="panel mt-4 space-y-6 p-4">
        <div v-for="bucket in groupedFull" :key="bucket.group">
          <h3 class="text-[12px] font-semibold text-graphite">{{ bucket.group }}</h3>
          <ul class="mt-2">
            <li
              v-for="entry in bucket.entries"
              :key="entry.id"
              class="flex items-center gap-3 border-b border-line py-2 last:border-b-0"
            >
              <span class="mono-value w-6 shrink-0 text-right text-[11px] text-graphite">
                {{ entry.rank }}
              </span>
              <SystemLogo
                :id="entry.id"
                :color="entry.color"
                :monogram="entry.monogram"
                :size="18"
                :radius="4"
              />
              <span class="min-w-0 flex-1 truncate text-[13px]">{{ entry.name }}</span>
              <span class="mono-value hidden shrink-0 text-[11px] text-graphite sm:inline">
                {{ entry.familyLabel }}
              </span>
              <span class="mono-value w-12 shrink-0 text-right text-[12px]">{{ entry.match }}%</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <ResultExtras :result="result" />
  </div>
</template>
