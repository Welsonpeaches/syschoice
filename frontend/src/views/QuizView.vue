<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check } from 'lucide-vue-next'
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
  <section v-if="currentSection">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="mono-value text-[11px] text-graphite">
          {{ t('quiz.section', { n: sectionIndex + 1, total: sections.length }) }}
        </p>
        <h1 class="mt-1.5 text-[22px] font-semibold">{{ currentSection.title }}</h1>
        <p class="mt-2 max-w-[58ch] text-[13px] text-graphite">{{ currentSection.desc }}</p>
      </div>
      <p class="mono-value text-[12px] text-graphite">
        {{ t('quiz.answered', { done: store.answeredCount, total: store.questions.length }) }}
      </p>
    </div>

    <div class="mt-5 h-[3px] w-full bg-paper-2">
      <div
        class="h-full bg-flux transition-[width] duration-300 ease-out"
        :style="{ width: `${progress}%` }"
      />
    </div>

    <div class="mt-8 space-y-9">
      <article v-for="(question, index) in sectionQuestions" :key="question.id">
        <header class="flex items-baseline gap-2.5">
          <span class="mono-value text-[12px] text-line-strong">
            {{ String(sectionIndex * 6 + index + 1).padStart(2, '0') }}
          </span>
          <h2 class="text-[15px] font-semibold">{{ question.title }}</h2>
        </header>
        <p v-if="question.help" class="mt-1.5 pl-[30px] text-[12px] text-graphite">
          {{ question.help }}
        </p>
        <p v-else-if="question.type === 'multi'" class="mt-1.5 pl-[30px] text-[12px] text-graphite">
          <template v-if="question.maxSelect">
            {{ t('quiz.maxHint', { n: question.maxSelect }) }}
          </template>
          <template v-else>{{ t('quiz.multiHint') }}</template>
        </p>

        <div v-if="question.type === 'scale'" class="mt-3 flex flex-wrap gap-2 pl-[30px]">
          <button
            v-for="option in question.options"
            :key="option.id"
            type="button"
            class="mono-value h-10 w-12 border text-[14px]"
            :class="
              store.answers[question.id] === option.value
                ? 'border-flux bg-flux text-white'
                : 'border-line-strong bg-white hover:border-ink'
            "
            @click="chooseScale(question, option.value as number)"
          >
            {{ option.label }}
          </button>
        </div>

        <ul v-else class="mt-3 border-t border-line pl-[30px]">
          <li v-for="option in question.options" :key="option.id" class="border-b border-line">
            <button
              type="button"
              class="flex w-full items-start gap-3 py-3 text-left"
              @click="choose(question, option.id)"
            >
              <span
                class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center border"
                :class="
                  isSelected(question, option.id)
                    ? 'border-flux bg-flux text-white'
                    : 'border-line-strong bg-white'
                "
              >
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
