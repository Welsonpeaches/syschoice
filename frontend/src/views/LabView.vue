<script setup lang="ts">
import { Check, Loader2, Search, Terminal } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { t } from '@/i18n'
import { useAssessmentStore } from '@/stores/assessment'

const router = useRouter()
const store = useAssessmentStore()
const tab = ref<'cli' | 'software' | 'scenario'>('cli')
const query = ref('')
const submitting = ref(false)

onMounted(async () => {
  await store.ensureLoaded()
})

const tabs = computed(() => [
  {
    id: 'cli' as const,
    label: t('lab.cli'),
    done: Object.keys(store.cli).length,
    total: store.catalog?.cli.length ?? 0,
    required: true,
  },
  {
    id: 'software' as const,
    label: t('lab.software'),
    done: store.software.length,
    total: store.catalog?.software.length ?? 0,
    required: false,
  },
  {
    id: 'scenario' as const,
    label: t('lab.scenario'),
    done: Object.keys(store.scenarios).length,
    total: store.catalog?.scenarios.length ?? 0,
    required: true,
  },
])

const softwareGroups = computed(() => {
  const catalog = store.catalog
  if (!catalog) return []
  const needle = query.value.trim().toLowerCase()
  return catalog.softwareCategories
    .map((category) => ({
      id: category.id,
      label: category.label,
      items: catalog.software.filter(
        (item) =>
          item.category === category.id &&
          (!needle ||
            item.name.toLowerCase().includes(needle) ||
            item.note.toLowerCase().includes(needle)),
      ),
    }))
    .filter((group) => group.items.length > 0)
})

const canSubmit = computed(() => store.cliComplete && store.scenarioComplete)

// The button stays disabled until both required modules are finished, so say
// exactly what is still outstanding instead of leaving a grey mystery.
const outstanding = computed(() => {
  const missing: string[] = []
  const cliTotal = store.catalog?.cli.length ?? 0
  const scenarioTotal = store.catalog?.scenarios.length ?? 0
  const cliDone = Object.keys(store.cli).length
  const scenarioDone = Object.keys(store.scenarios).length
  if (cliTotal && cliDone < cliTotal) missing.push(`命令行小测还差 ${cliTotal - cliDone} 题`)
  if (scenarioTotal && scenarioDone < scenarioTotal) {
    missing.push(`情景决策还差 ${scenarioTotal - scenarioDone} 题`)
  }
  return missing
})

async function submit() {
  submitting.value = true
  const data = await store.submit()
  submitting.value = false
  if (data) router.push({ name: 'result', params: { code: data.shareCode } })
}
</script>

<template>
  <section data-view="lab">
    <h1 class="text-[22px] font-semibold">{{ t('lab.title') }}</h1>

    <div class="mt-5 inline-flex gap-1 rounded-card bg-paper-2 p-1">
      <button
        v-for="item in tabs"
        :key="item.id"
        type="button"
        class="flex items-center gap-2 rounded-[6px] px-4 py-2 text-[13px] transition-all"
        :class="
          tab === item.id
            ? 'bg-surface font-semibold text-ink shadow-panel'
            : 'text-graphite hover:text-ink'
        "
        @click="tab = item.id"
      >
        {{ item.label }}
        <span
          class="mono-value rounded-full px-1.5 text-[10px] leading-[16px]"
          :class="
            item.required && item.done >= item.total && item.total > 0
              ? 'bg-flux text-white'
              : item.required
                ? 'bg-amber-soft text-amber'
                : 'bg-paper-2 text-graphite'
          "
        >
          {{ item.done }}/{{ item.total }}
        </span>
      </button>
    </div>

    <!-- ------------------------------------------------------ 命令行小测 -->
    <div v-if="tab === 'cli'" class="mt-7">
      <p class="max-w-[58ch] text-[13px] text-graphite">{{ t('lab.cliDesc') }}</p>
      <div class="mt-6 space-y-7">
        <article v-for="question in store.catalog?.cli ?? []" :key="question.id">
          <div class="rounded-card border border-ink-soft bg-ink px-4 py-3 shadow-panel">
            <div class="mono-value flex items-center gap-2 text-[13px] text-white/90">
              <Terminal :size="14" class="text-flux-soft" />
              <span>{{ question.prompt }}</span>
            </div>
          </div>
          <h2 class="mt-3 text-[14px] font-semibold">{{ question.title }}</h2>
          <ul class="mt-2 space-y-2">
            <li v-for="option in question.options" :key="option.id">
              <button
                type="button"
                class="option-card option-card--round"
                :class="store.cli[question.id] === option.id ? 'option-card--on' : ''"
                @click="store.setCli(question.id, option.id)"
              >
                <span class="option-mark">
                  <Check
                    v-if="store.cli[question.id] === option.id"
                    :size="11"
                    :stroke-width="3"
                  />
                </span>
                <span class="text-[14px]">{{ option.label }}</span>
              </button>
            </li>
          </ul>
        </article>
      </div>
    </div>

    <!-- ------------------------------------------------------- 软件自检 -->
    <div v-else-if="tab === 'software'" class="mt-7">
      <p class="max-w-[58ch] text-[13px] text-graphite">{{ t('lab.softwareDesc') }}</p>

      <label
        class="mt-5 flex items-center gap-2 rounded-card border border-line-strong bg-surface px-3 py-2 transition-shadow focus-within:border-flux focus-within:shadow-[0_0_0_3px_var(--color-flux-soft)]"
      >
        <Search :size="15" class="text-graphite" />
        <input
          v-model="query"
          class="w-full bg-transparent text-[13px] outline-none"
          :placeholder="t('lab.search')"
        />
      </label>

      <p v-if="store.software.length" class="mt-3 flex items-center gap-2">
        <span class="pill !border-flux !bg-flux-soft !text-flux-deep">
          {{ t('common.selected') }} {{ store.software.length }}
        </span>
      </p>

      <div class="mt-5 space-y-6">
        <div v-for="group in softwareGroups" :key="group.id">
          <h2 class="text-[12px] font-semibold text-graphite">{{ group.label }}</h2>
          <ul class="mt-2 grid gap-2 sm:grid-cols-2">
            <li v-for="item in group.items" :key="item.id">
              <button
                type="button"
                class="option-card !py-2.5"
                :class="store.software.includes(item.id) ? 'option-card--on' : ''"
                @click="store.toggleSoftware(item.id)"
              >
                <span class="option-mark">
                  <Check v-if="store.software.includes(item.id)" :size="11" :stroke-width="3" />
                </span>
                <span class="min-w-0">
                  <span class="block text-[13px]">{{ item.name }}</span>
                  <span v-if="item.note" class="mt-0.5 block text-[11px] text-graphite">
                    {{ item.note }}
                  </span>
                </span>
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ------------------------------------------------------- 情景决策 -->
    <div v-else class="mt-7">
      <p class="max-w-[58ch] text-[13px] text-graphite">{{ t('lab.scenarioDesc') }}</p>
      <div class="mt-6 space-y-7">
        <article v-for="question in store.catalog?.scenarios ?? []" :key="question.id">
          <h2 class="text-[14px] font-semibold">{{ question.title }}</h2>
          <p v-if="question.context" class="mt-1 text-[12px] text-graphite">
            {{ question.context }}
          </p>
          <ul class="mt-2 space-y-2">
            <li v-for="option in question.options" :key="option.id">
              <button
                type="button"
                class="option-card option-card--round"
                :class="store.scenarios[question.id] === option.id ? 'option-card--on' : ''"
                @click="store.setScenario(question.id, option.id)"
              >
                <span class="option-mark">
                  <Check
                    v-if="store.scenarios[question.id] === option.id"
                    :size="11"
                    :stroke-width="3"
                  />
                </span>
                <span class="text-[14px]">{{ option.label }}</span>
              </button>
            </li>
          </ul>
        </article>
      </div>
    </div>

    <div class="panel mt-9 flex flex-wrap items-center justify-between gap-4 p-4">
      <ul class="flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px]">
        <li
          v-for="item in tabs"
          :key="item.id"
          class="flex items-center gap-2"
          :class="item.required ? 'text-ink' : 'text-graphite'"
        >
          <Check
            v-if="item.total > 0 && item.done >= item.total"
            :size="13"
            :stroke-width="3"
            class="text-flux"
          />
          <span
            v-else-if="item.required"
            class="h-2.5 w-2.5 rounded-full bg-amber"
          />
          <span v-else class="h-2.5 w-2.5 rounded-full border border-line-strong" />
          {{ item.label }}
          <span class="mono-value text-graphite">{{ item.done }}/{{ item.total }}</span>
          <span v-if="!item.required" class="text-mist">可选</span>
        </li>
      </ul>
      <button type="button" class="btn-primary" :disabled="!canSubmit || submitting" @click="submit">
        <Loader2 v-if="submitting" :size="16" class="animate-spin" />
        {{ submitting ? '正在计算…' : '生成推荐结果' }}
      </button>
    </div>

    <p v-if="outstanding.length" class="mt-2.5 text-[12px] text-amber">
      还需要完成：{{ outstanding.join('、') }}
    </p>

    <p
      v-if="store.error"
      class="mt-4 rounded-card border border-alert bg-alert-soft px-4 py-3 text-[13px] text-alert"
    >
      {{ store.error }}
    </p>
  </section>
</template>
