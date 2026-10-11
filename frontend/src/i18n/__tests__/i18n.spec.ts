import { describe, expect, it } from 'vitest'

import { t } from '@/i18n'

describe('i18n', () => {
  it('interpolates named parameters', () => {
    expect(t('quiz.answered', { done: 3, total: 28 })).toBe('已答 3 / 28')
  })

  it('falls back to the key when a string is missing', () => {
    expect(t('this.key.does.not.exist')).toBe('this.key.does.not.exist')
  })
})
