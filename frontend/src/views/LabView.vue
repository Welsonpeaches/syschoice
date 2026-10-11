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
  { id: 'cli' as const, label: t('lab.cli') },
  { id: 'software' as const, label: t('lab.software') },
  { id: 'scenario' as const, label: t('lab.scenario') },
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

async function submit() {
  submitting.value = true
  const data = await store.submit()
  submitting.value = false
  if (data) router.push({ name: 'result', params: { code: data.shareCode } })
}
</script>

<template>
  <section>
    <h1 class="text-[22px] font-semibold">{{ t('lab.title') }}</h1>

    <div class="mt-5 flex gap-1 border-b border-line">
      <button
        v-for="item in tabs"
        :key="item.id"
        type="button"
        class="-mb-px border-b-2 px-4 py-2.5 text-[13px]"
        :class="
          tab === item.id
            ? 'border-flux font-semibold text-ink'
            : 'border-transparent text-graphite hover:text-ink'
        "
        @click="tab = item.id"
      >
        {{ item.label }}
      </button>
    </div>

    <!-- ------------------------------------------------------ 命令行小测 -->
    <div v-if="tab === 'cli'" class="mt-7">
      <p class="max-w-[58ch] text-[13px] text-graphite">{{ t('lab.cliDesc') }}</p>
      <div class="mt-6 space-y-7">
        <article v-for="question in store.catalog?.cli ?? []" :key="question.id">
          <div class="border border-line bg-ink px-4 py-3">
            <div class="mono-value flex items-center gap-2 text-[13px] text-white/90">
              <Terminal :size="14" class="text-flux-soft" />
              <span>{{ question.prompt }}</span>
            </div>
          </div>
          <h2 class="mt-3 text-[14px] font-semibold">{{ question.title }}</h2>
          <ul class="mt-2 border-t border-line">
            <li v-for="option in question.options" :key="option.id" class="border-b border-line">
              <button
                type="button"
                class="flex w-full items-start gap-3 py-3 text-left"
                @click="store.setCli(question.id, option.id)"
              >
                <span
                  class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center border"
                  :class="
                    store.cli[question.id] === option.id
                      ? 'border-flux bg-flux text-white'
                      : 'border-line-strong bg-white'
                  "
                >
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

      <label class="mt-5 flex items-center gap-2 border border-line-strong bg-white px-3 py-2">
        <Search :size="15" class="text-graphite" />
        <input
          v-model="query"
          class="w-full bg-transparent text-[13px] outline-none"
          :placeholder="t('lab.search')"
        />
      </label>

      <p v-if="store.software.length" class="mono-value mt-3 text-[12px] text-graphite">
        {{ t('common.selected') }} {{ store.software.length }}
      </p>

      <div class="mt-5 space-y-6">
        <div v-for="group in softwareGroups" :key="group.id">
          <h2 class="text-[12px] font-semibold text-graphite">{{ group.label }}</h2>
          <ul class="mt-2 grid gap-x-6 sm:grid-cols-2">
            <li v-for="item in group.items" :key="item.id" class="border-t border-line">
              <button
                type="button"
                class="flex w-full items-start gap-3 py-2.5 text-left"
                @click="store.toggleSoftware(item.id)"
              >
                <span
                  class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center border"
                  :class="
                    store.software.includes(item.id)
                      ? 'border-flux bg-flux text-white'
                      : 'border-line-strong bg-white'
                  "
                >
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
          <ul class="mt-2 border-t border-line">
            <li v-for="option in question.options" :key="option.id" class="border-b border-line">
              <button
                type="button"
                class="flex w-full items-start gap-3 py-3 text-left"
                @click="store.setScenario(question.id, option.id)"
              >
                <span
                  class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center border"
                  :class="
                    store.scenarios[question.id] === option.id
                      ? 'border-flux bg-flux text-white'
                      : 'border-line-strong bg-white'
                  "
                >
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

    <div class="mt-9 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-6">
      <p class="text-[12px] text-graphite">
        命令行 {{ Object.keys(store.cli).length }} / {{ store.catalog?.cli.length ?? 0 }} ·
        情景 {{ Object.keys(store.scenarios).length }} / {{ store.catalog?.scenarios.length ?? 0 }}
      </p>
      <button type="button" class="btn-primary" :disabled="!canSubmit || submitting" @click="submit">
        <Loader2 v-if="submitting" :size="16" class="animate-spin" />
        {{ submitting ? '正在计算…' : '生成推荐结果' }}
      </button>
    </div>

    <p v-if="store.error" class="mt-4 border border-alert bg-alert-soft px-4 py-3 text-[13px] text-alert">
      {{ store.error }}
    </p>
  </section>
</template>
