<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, Loader2 } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import type { Question } from '@/api/types'
import { t } from '@/i18n'
import { useAssessmentStore } from '@/stores/assessment'

const router = useRouter()
const store = useAssessmentStore()
const sectionIndex = ref(0)

onMounted(async () => {
  await store.ensureLoaded()
})

const sections = computed(() => store.sections)
const currentSection = computed(() => sections.value[sectionIndex.value])

const sectionQuestions = computed<Question[]>(() =>
  store.questions.filter((question) => question.section === currentSection.value?.id),
)

const progress = computed(() => {
  const total = store.questions.length
  return total ? Math.round((store.answeredCount / total) * 100) : 0
})

// Per-section fill is more informative than a single bar, and it shows how far
// through the current block you are.
const sectionFill = computed(() =>
  sections.value.map((section) => {
    const questions = store.questions.filter((question) => question.section === section.id)
    const done = questions.filter((question) => {
      const value = store.answers[question.id]
      return Array.isArray(value) ? value.length > 0 : value !== undefined
    }).length
    return questions.length ? done / questions.length : 0
  }),
)

const isLast = computed(() => sectionIndex.value >= sections.value.length - 1)

const sectionDone = computed(() =>
  sectionQuestions.value.every((question) => {
    const value = store.answers[question.id]
    return Array.isArray(value) ? value.length > 0 : value !== undefined
  }),
)

function isSelected(question: Question, optionId: string) {
  const value = store.answers[question.id]
  return Array.isArray(value) ? value.includes(optionId) : value === optionId
}

function choose(question: Question, optionId: string) {
  if (question.type === 'multi') store.toggleMulti(question.id, optionId, question.maxSelect)
  else store.setAnswer(question.id, optionId)
}

function chooseScale(question: Question, value: number) {
  store.setAnswer(question.id, value)
}

function back() {
  if (sectionIndex.value === 0) router.push({ name: 'hardware' })
  else sectionIndex.value -= 1
}

function next() {
  if (isLast.value) router.push({ name: 'lab' })
  else sectionIndex.value += 1
}

watch(sectionIndex, () => {
  window.scrollTo({ top: 0 })
})
</script>

<template>
  <div
    v-if="!currentSection"
    data-view="quiz"
    class="panel flex items-center gap-3 p-6 text-[13px] text-graphite"
  >
    <Loader2 :size="16" class="animate-spin" />
    {{ t('common.loading') }}
  </div>

  <section v-else data-view="quiz">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="flex items-center gap-2">
          <span
            class="mono-value flex h-5 items-center rounded-full bg-flux px-2 text-[11px] font-medium text-white"
          >
            {{ sectionIndex + 1 }}/{{ sections.length }}
          </span>
        </p>
        <h1 class="mt-2 text-[26px] font-semibold">{{ currentSection.title }}</h1>
        <p class="mt-2 max-w-[58ch] text-[13px] text-graphite">{{ currentSection.desc }}</p>
      </div>
      <p class="mono-value text-[12px] text-graphite">
        {{ t('quiz.answered', { done: store.answeredCount, total: store.questions.length }) }}
      </p>
    </div>

    <div class="mt-5 flex gap-1.5" role="progressbar" :aria-valuenow="progress">
      <div
        v-for="(fill, index) in sectionFill"
        :key="index"
        class="h-[5px] flex-1 overflow-hidden rounded-full bg-paper-2"
      >
        <div
          class="h-full rounded-full bg-flux transition-[width] duration-300 ease-out"
          :style="{ width: `${fill * 100}%` }"
        />
      </div>
    </div>

    <div class="mt-8 space-y-9">
      <article v-for="(question, index) in sectionQuestions" :key="question.id">
        <header class="flex items-baseline gap-2.5">
          <span
            class="mono-value flex h-5 w-6 shrink-0 items-center justify-center rounded-sm bg-paper-2 text-[11px] text-graphite"
          >
            {{ String(sectionIndex * 6 + index + 1).padStart(2, '0') }}
          </span>
          <h2 class="text-[15px] font-semibold">{{ question.title }}</h2>
        </header>
        <p v-if="question.help" class="mt-1.5 pl-[34px] text-[12px] text-graphite">
          {{ question.help }}
        </p>
        <p v-else-if="question.type === 'multi'" class="mt-1.5 pl-[34px] text-[12px] text-graphite">
          <template v-if="question.maxSelect">
            {{ t('quiz.maxHint', { n: question.maxSelect }) }}
          </template>
          <template v-else>{{ t('quiz.multiHint') }}</template>
        </p>

        <div v-if="question.type === 'scale'" class="mt-3 pl-[34px]">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="option in question.options"
              :key="option.id"
              type="button"
              class="mono-value h-11 w-13 min-w-[52px] rounded-card border text-[15px] transition-all"
              :class="
                store.answers[question.id] === option.value
                  ? 'border-flux bg-flux text-white shadow-panel'
                  : 'border-line-strong bg-surface text-graphite hover:-translate-y-px hover:border-flux hover:text-flux-deep hover:shadow-panel'
              "
              @click="chooseScale(question, option.value as number)"
            >
              {{ option.label }}
            </button>
          </div>
          <div class="mt-2 flex w-full max-w-[320px] justify-between text-[11px] text-mist">
            <span>拿来就用</span>
            <span>折腾是乐趣</span>
          </div>
        </div>

        <ul v-else class="mt-3 space-y-2 pl-[34px]">
          <li v-for="option in question.options" :key="option.id">
            <button
              type="button"
              class="option-card"
              :class="[
                isSelected(question, option.id) ? 'option-card--on' : '',
                question.type === 'single' ? 'option-card--round' : '',
              ]"
              @click="choose(question, option.id)"
            >
              <span class="option-mark">
                <Check v-if="isSelected(question, option.id)" :size="11" :stroke-width="3" />
              </span>
              <span class="min-w-0">
                <span class="block text-[14px]">{{ option.label }}</span>
                <span v-if="option.desc" class="mt-0.5 block text-[12px] text-graphite">
                  {{ option.desc }}
                </span>
              </span>
            </button>
          </li>
        </ul>
      </article>
    </div>

    <div class="mt-9 flex items-center justify-between gap-3 border-t border-line pt-6">
      <button type="button" class="btn-quiet" @click="back">
        <ArrowLeft :size="15" />
        {{ t('common.prev') }}
      </button>
      <button type="button" class="btn-primary" :disabled="!sectionDone" @click="next">
        {{ isLast ? t('common.next') : t('common.next') }}
        <ArrowRight :size="16" />
      </button>
    </div>
  </section>
</template>
