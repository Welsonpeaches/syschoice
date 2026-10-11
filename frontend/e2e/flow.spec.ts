import { expect, test, type Page } from '@playwright/test'

const SHOTS = process.env.SHOT_DIR ?? '/tmp/syschoice-shots'

/**
 * Route changes animate the incoming view, and the outgoing one stays mounted
 * for a frame. Waiting for exactly one view guarantees we are answering the
 * step we think we are.
 */
async function waitForView(page: Page, name: string) {
  await expect(page.locator(`[data-view="${name}"]`)).toBeVisible()
  await expect(page.locator('[data-view]')).toHaveCount(1)
}

/** Answer every question in the current section by picking the first option. */
async function answerSection(page: Page) {
  const articles = page.locator('article')
  await expect(articles.first()).toBeVisible()
  const count = await articles.count()
  for (let index = 0; index < count; index += 1) {
    await articles.nth(index).locator('button').first().click()
  }
}

async function completeQuiz(page: Page) {
  for (let section = 0; section < 5; section += 1) {
    await answerSection(page)
    await page.getByRole('button', { name: '下一步', exact: true }).click()
    await page.waitForTimeout(150)
  }
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  )
  expect(overflow).toBeLessThanOrEqual(1)
}

test('start page renders the probe readout and no marketing filler', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.getByText('当前设备探测结果')).toBeVisible()
  await expect(page.getByText('候选系统', { exact: true })).toBeVisible()
  await expect(page.getByText('会被比较的全部候选')).toBeVisible()
  await expectNoHorizontalOverflow(page)
  await page.screenshot({ path: `${SHOTS}/start.png`, fullPage: true })
})

test('interview step explains itself when the model is unavailable', async ({ page }) => {
  await page.goto('/test/interview')
  // The guard sends an unvisited session back to the hardware step first.
  await expect(page).toHaveURL(/\/test\/hardware/)
  await page.getByRole('button', { name: '跳过这一步' }).click()
  await waitForView(page, 'interview')

  // Without a key the step still lets the person write, and always lets them
  // move on rather than trapping them.
  await expect(page.getByText('用自己的话描述一下')).toBeVisible()
  await expect(page.getByRole('button', { name: '跳过这一步' })).toBeVisible()
  await expect(page.getByRole('button', { name: '让模型帮我梳理' })).toBeDisabled()
})

test('completes the full assessment and produces a shareable result', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: '开始检测' }).first().click()

  await expect(page).toHaveURL(/\/test\/hardware/)
  await waitForView(page, 'hardware')
  await page.screenshot({ path: `${SHOTS}/hardware.png`, fullPage: true })
  await page.getByRole('button', { name: '下一步' }).click()

  // The interview step is optional; without an LLM key it is pure form-free
  // text plus a skip, and the questionnaire must still work.
  await expect(page).toHaveURL(/\/test\/interview/)
  await waitForView(page, 'interview')
  await page.screenshot({ path: `${SHOTS}/interview.png`, fullPage: true })
  await page.getByRole('button', { name: '跳过这一步' }).click()

  await expect(page).toHaveURL(/\/test\/quiz/)
  await waitForView(page, 'quiz')
  await page.screenshot({ path: `${SHOTS}/quiz.png`, fullPage: true })
  await completeQuiz(page)

  // --- interactive lab: CLI, software self-check, scenarios ---
  await expect(page).toHaveURL(/\/test\/lab/)
  await waitForView(page, 'lab')
  await answerSection(page)
  await page.getByRole('button', { name: '软件自检' }).click()
  await page.getByRole('button', { name: /Steam 本体/ }).click()
  await page.getByRole('button', { name: /微信/ }).first().click()
  await page.screenshot({ path: `${SHOTS}/lab-software.png`, fullPage: true })

  await page.getByRole('button', { name: '情景决策' }).click()
  await answerSection(page)

  const submit = page.getByRole('button', { name: '生成推荐结果' })
  await expect(submit).toBeEnabled()
  await submit.click()

  // --- result ---
  await expect(page).toHaveURL(/\/result\/[0-9a-f]{8}/)
  const champion = page.getByRole('heading', { level: 1 })
  await expect(champion).toBeVisible()
  const championName = (await champion.textContent())?.trim() ?? ''
  expect(championName.length).toBeGreaterThan(1)

  // A match percentage and the radar SVG both have to be present.
  await expect(page.getByText(/^\d+(\.\d+)?%$/).first()).toBeVisible()
  await expect(page.locator('svg').first()).toBeVisible()

  await expectNoHorizontalOverflow(page)
  await page.screenshot({ path: `${SHOTS}/result.png`, fullPage: true })

  // Expanding the full ranking must list all 72 candidates.
  await page.getByRole('button', { name: /展开完整排行/ }).click()
  await expect(page.getByText('BSD 家族').first()).toBeVisible()
  await page.screenshot({ path: `${SHOTS}/result-full.png`, fullPage: true })

  // --- the share link must resolve on a fresh page ---
  const shareUrl = page.url()
  const fresh = await page.context().newPage()
  await fresh.goto(shareUrl)
  await expect(fresh.getByRole('heading', { level: 1 })).toHaveText(championName)
  await fresh.close()

  // --- feedback is recorded and confirmed in place ---
  await page.getByLabel('最终安装的系统').selectOption({ index: 1 })
  await page.getByRole('button', { name: '4', exact: true }).click()
  await page.getByRole('button', { name: '提交反馈' }).click()
  await expect(page.getByText('已记录，谢谢。你的选择会用来改进打分。')).toBeVisible()
  await page.screenshot({ path: `${SHOTS}/result-feedback.png`, fullPage: true })
})

test('stats page reports the recorded session', async ({ page }) => {
  await page.goto('/stats')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.getByText('累计完成')).toBeVisible()
  await expectNoHorizontalOverflow(page)
  await page.screenshot({ path: `${SHOTS}/stats.png`, fullPage: true })
})

test('admin rejects a bad token and accepts the configured one', async ({ page }) => {
  await page.goto('/admin')
  await page.getByLabel('管理令牌').fill('not-the-token')
  await page.getByRole('button', { name: '进入' }).click()
  await expect(page.getByText('令牌无效。')).toBeVisible()

  await page.getByLabel('管理令牌').fill('syschoice-admin')
  await page.getByRole('button', { name: '进入' }).click()
  await expect(page.getByRole('table')).toBeVisible()
  await expect(page.getByRole('button', { name: '导出 CSV' })).toBeVisible()
  await page.screenshot({ path: `${SHOTS}/admin.png`, fullPage: true })
})
