<script setup lang="ts">
import { ArrowLeft, ArrowRight, Loader2, Sparkles, X } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '@/api/client'
import { t } from '@/i18n'
import { useAssessmentStore } from '@/stores/assessment'

const router = useRouter()
const store = useAssessmentStore()

const text = ref(store.interviewText)
const answers = ref<string[]>(store.followups.map(() => ''))
const busy = ref(false)
const error = ref<string | null>(null)
const ranOnce = computed(() => store.interview.length > 0)

const dimensionLabels: Record<string, string> = {
  ease: '易用',
  stability: '稳定',
  gaming: '游戏',
  creative: '创作',
  office: '办公',
  dev: '开发',
  customization: '可定制',
  privacy: '隐私',
  lightweight: '轻量',
}

const traitLabels: Record<string, string> = {
  gaming_intensity: '游戏强度',
  tinker: '折腾意愿',
  tech_level: '技术水平',
  office_need: '办公需求',
  creative_need: '创作需求',
  dev_need: '开发需求',
  privacy_need: '隐私需求',
  stability_pref: '稳定偏好',
  customization_need: '掌控欲',
  budget_sensitive: '预算敏感',
  security_interest: '安全兴趣',
  server_interest: '服务器兴趣',
  apple_ecosystem: 'Apple 生态',
  support_need: '支持需求',
}

const chips = computed(() => {
  const merged = new Map<string, string>()
  for (const item of store.interview) {
    for (const [key, value] of Object.entries(item.traits)) {
      merged.set(`trait:${key}`, `${traitLabels[key] ?? key} ${Math.round(value * 100)}%`)
    }
    for (const [key, value] of Object.entries(item.dimensionTargets)) {
      merged.set(`dim:${key}`, `${dimensionLabels[key] ?? key} 期望 ${Math.round(value)}`)
    }
    for (const sid of item.software) merged.set(`sw:${sid}`, sid)
  }
  return [...merged.values()]
})

onMounted(async () => {
  await store.ensureLoaded()
})

async function ask() {
  if (!text.value.trim()) return
  busy.value = true
  error.value = null
  try {
    // Later rounds also carry the previous answers so the model can refine.
    const history = store.followups
      .map((question, index) => ({ question, answer: answers.value[index] ?? '' }))
      .filter((turn) => turn.answer.trim())

    const data = await api.interview(text.value, history)
    store.interviewText = text.value
    store.addEvidence(data.evidence)
    store.followups = data.followups
    answers.value = data.followups.map(() => '')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '请求失败'
  } finally {
    busy.value = false
  }
}

function next() {
  router.push({ name: 'quiz' })
}
</script>

<template>
  <section data-view="interview">
    <h1 class="text-[22px] font-semibold">{{ t('interview.title') }}</h1>
    <p class="mt-2 max-w-[60ch] text-[13px] text-graphite">{{ t('interview.desc') }}</p>

    <div class="panel mt-6 p-4">
      <label class="block">
        <span class="text-[12px] text-graphite">你的情况</span>
        <textarea
          v-model="text"
          rows="4"
          class="field-input mt-1.5 resize-none !font-sans"
          :placeholder="t('interview.placeholder')"
        />
      </label>

      <div class="mt-3 flex flex-wrap items-center gap-3">
        <button type="button" class="btn-primary" :disabled="busy || !text.trim()" @click="ask">
          <Loader2 v-if="busy" :size="15" class="animate-spin" />
          <Sparkles v-else :size="15" />
          {{ busy ? '正在梳理…' : ranOnce ? t('interview.again') : t('interview.ask') }}
        </button>
        <button
          v-if="ranOnce"
          type="button"
          class="btn-quiet"
          @click="store.clearInterview()"
        >
          {{ t('interview.clear') }}
        </button>
      </div>

      <p v-if="error" class="mt-3 rounded-card border border-alert bg-alert-soft px-3 py-2 text-[12px] text-alert">
        {{ error }}
      </p>
    </div>

    <div v-if="store.followups.length" class="panel mt-4 p-4">
      <h2 class="text-[13px] font-semibold">{{ t('interview.followups') }}</h2>
      <ul class="mt-3 space-y-2">
        <li v-for="(question, index) in store.followups" :key="question" class="flex gap-3">
          <span class="mono-value mt-2.5 text-[12px] text-line-strong">{{ index + 1 }}</span>
          <span class="mt-2 text-[13px]">{{ question }}</span>
        </li>
      </ul>
      <label class="mt-3 block">
        <span class="text-[12px] text-graphite">{{ t('interview.answer') }}</span>
        <textarea
          v-model="answers[0]"
          rows="3"
          class="field-input mt-1.5 resize-none !font-sans"
          placeholder="把回答写在这里，然后点上面的「再补充一轮」"
        />
      </label>
    </div>

    <div v-if="ranOnce" class="panel mt-4 p-4">
      <h2 class="text-[13px] font-semibold">{{ t('interview.understood') }}</h2>
      <ul v-if="chips.length" class="mt-3 flex flex-wrap gap-2">
        <li v-for="chip in chips" :key="chip" class="pill !border-flux !bg-flux-soft !text-flux-deep">
          {{ chip }}
        </li>
      </ul>
      <p v-else class="mt-2 text-[12px] text-graphite">{{ t('interview.none') }}</p>

      <ul v-if="store.interviewNotes.length" class="mt-3 space-y-1.5">
        <li
          v-for="note in store.interviewNotes"
          :key="note"
          class="flex gap-2 text-[12px] text-graphite"
        >
          <span class="mt-[7px] h-[5px] w-[5px] shrink-0 rounded-full bg-flux" />
          {{ note }}
        </li>
      </ul>
    </div>

    <div class="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-6">
      <button type="button" class="btn-quiet" @click="router.push({ name: 'hardware' })">
        <ArrowLeft :size="15" />
        {{ t('common.prev') }}
      </button>
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="text-[13px] text-graphite underline decoration-dotted hover:text-ink"
          @click="next"
        >
          {{ t('common.skip') }}
        </button>
        <button type="button" class="btn-primary" @click="next">
          {{ t('common.next') }}
          <ArrowRight :size="16" />
        </button>
      </div>
    </div>
  </section>
</template>
