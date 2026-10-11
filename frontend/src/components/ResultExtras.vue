<script setup lang="ts">
import { Loader2, Sparkles } from 'lucide-vue-next'
import { computed, ref } from 'vue'

import { api } from '@/api/client'
import type { AssessResult } from '@/api/types'

const props = defineProps<{ result: AssessResult }>()
const emit = defineEmits<{ (event: 'feedback', value: NonNullable<AssessResult['feedback']>): void }>()

// ---------------------------------------------------------------- LLM 点评
const insight = ref<string | null>(props.result.insight ?? null)
const insightModel = ref<string | null>(props.result.insightModel ?? null)
const insightBusy = ref(false)
const insightError = ref<string | null>(null)

const feedback = ref(props.result.feedback ?? null)
// Default to the recommended system; the person can pick any of the 72.
const chosenId = ref<string>(props.result.feedback?.chosen_id ?? props.result.top[0]?.id ?? '')
const satisfaction = ref<number | null>(props.result.feedback?.satisfaction ?? null)
const note = ref<string>(props.result.feedback?.note ?? '')
const feedbackBusy = ref(false)
const feedbackError = ref<string | null>(null)
const feedbackSaved = ref(false)

const groupedOptions = computed(() => {
  const familyOrder = ['windows', 'macos', 'linux', 'bsd']
  const buckets = new Map<string, { label: string; items: { id: string; name: string }[] }>()
  for (const entry of props.result.full) {
    if (!buckets.has(entry.family)) {
      buckets.set(entry.family, { label: entry.familyLabel, items: [] })
    }
    buckets.get(entry.family)!.items.push({ id: entry.id, name: entry.name })
  }
  return familyOrder.filter((family) => buckets.has(family)).map((family) => buckets.get(family)!)
})

const canSendFeedback = computed(
  () => Boolean(chosenId.value) || satisfaction.value !== null || note.value.trim().length > 0,
)

async function generateInsight() {
  insightBusy.value = true
  insightError.value = null
  try {
    const data = await api.insight(props.result.shareCode)
    insight.value = data.insight
    insightModel.value = data.model
  } catch (err) {
    insightError.value = err instanceof Error ? err.message : '生成失败'
  } finally {
    insightBusy.value = false
  }
}

async function submitFeedback() {
  feedbackBusy.value = true
  feedbackError.value = null
  try {
    const data = await api.sendFeedback(props.result.shareCode, {
      chosenId: chosenId.value || null,
      satisfaction: satisfaction.value,
      note: note.value.trim() || null,
    })
    feedback.value = data.feedback
    feedbackSaved.value = true
    emit('feedback', data.feedback)
  } catch (err) {
    feedbackError.value = err instanceof Error ? err.message : '提交失败'
  } finally {
    feedbackBusy.value = false
  }
}
</script>

<template>
  <section class="mt-8 grid gap-6 lg:grid-cols-2">
    <!-- Optional model-written commentary; hidden entirely when unconfigured. -->
    <div v-if="result.llmEnabled" class="panel flex flex-col p-5">
      <h2 class="flex items-center gap-2 text-[13px] font-semibold">
        <Sparkles :size="15" class="text-flux" />
        让模型把这份结果讲一遍
      </h2>
      <p class="mt-1.5 text-[12px] text-graphite">
        模型只负责把已经算好的排名写成一段话，不会改变结论。
      </p>

      <div v-if="insight" class="mt-3 rounded-card border border-line bg-surface-2 p-3">
        <p class="text-[13px] leading-relaxed">{{ insight }}</p>
        <p v-if="insightModel" class="mono-value mt-2 text-[11px] text-mist">
          {{ insightModel }}
        </p>
      </div>

      <div v-else class="mt-3 flex-1">
        <button type="button" class="btn-primary" :disabled="insightBusy" @click="generateInsight">
          <Loader2 v-if="insightBusy" :size="15" class="animate-spin" />
          {{ insightBusy ? '正在生成…' : '生成点评' }}
        </button>
        <p v-if="insightError" class="mt-2 text-[12px] text-alert">{{ insightError }}</p>
      </div>
    </div>

    <!-- The only real label the project can collect: what did you install? -->
    <div class="panel p-5">
      <h2 class="text-[13px] font-semibold">你最后装了哪个？</h2>
      <p class="mt-1.5 text-[12px] text-graphite">
        这条反馈会匿名保存，用来把推荐权重调得更准。
      </p>

      <div v-if="feedbackSaved" class="mt-3 rounded-card border border-flux bg-flux-soft p-3">
        <p class="text-[13px] text-flux-deep">已记录，谢谢。你的选择会用来改进打分。</p>
        <p class="mono-value mt-1 text-[11px] text-graphite">
          {{ feedback?.chosen_name ?? '未选择系统' }} ·
          {{ feedback?.satisfaction ? `满意度 ${feedback.satisfaction}/5` : '未评分' }}
        </p>
      </div>

      <template v-else>
        <label class="mt-3 block">
          <span class="text-[12px] text-graphite">最终安装的系统</span>
          <select v-model="chosenId" class="field-input mt-1.5">
            <option value="">还没决定</option>
            <optgroup
              v-for="group in groupedOptions"
              :key="group.label"
              :label="`${group.label}（${group.items.length}）`"
            >
              <option v-for="option in group.items" :key="option.id" :value="option.id">
                {{ option.name }}
              </option>
            </optgroup>
          </select>
        </label>

        <div class="mt-3">
          <span class="text-[12px] text-graphite">用起来怎么样</span>
          <div class="mt-1.5 flex gap-1.5">
            <button
              v-for="score in [1, 2, 3, 4, 5]"
              :key="score"
              type="button"
              class="mono-value h-9 w-9 rounded-card border text-[13px] transition-all"
              :class="
                satisfaction === score
                  ? 'border-flux bg-flux text-white'
                  : 'border-line-strong bg-surface text-graphite hover:border-flux'
              "
              @click="satisfaction = score"
            >
              {{ score }}
            </button>
          </div>
        </div>

        <label class="mt-3 block">
          <span class="text-[12px] text-graphite">补充说明（可选）</span>
          <textarea
            v-model="note"
            rows="2"
            class="field-input mt-1.5 resize-none"
            placeholder="例如：驱动没问题，但网银还是用不了"
          />
        </label>

        <div class="mt-3 flex items-center gap-3">
          <button
            type="button"
            class="btn-quiet"
            :disabled="!canSendFeedback || feedbackBusy"
            @click="submitFeedback"
          >
            <Loader2 v-if="feedbackBusy" :size="15" class="animate-spin" />
            提交反馈
          </button>
          <p v-if="feedbackError" class="text-[12px] text-alert">{{ feedbackError }}</p>
        </div>
      </template>
    </div>
  </section>
</template>
