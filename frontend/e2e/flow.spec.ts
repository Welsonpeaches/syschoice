import { expect, test, type Page } from '@playwright/test'

const SHOTS = process.env.SHOT_DIR ?? '/tmp/syschoice-shots'

/** Answer every question in the current section by picking the first option. */
async function answerSection(page: Page) {
  const articles = page.locator('article')
  const count = await articles.count()
  for (let index = 0; index < count; index += 1) {
    await articles.nth(index).locator('button').first().click()
  }
}

async function completeQuiz(page: Page) {
  for (let section = 0; section < 5; section += 1) {
    await answerSection(page)
    await page.getByRole('button', { name: '下一步', exact: true }).click()
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
  await expect(page.getByText('候选系统')).toBeVisible()
  await expectNoHorizontalOverflow(page)
  await page.screenshot({ path: `${SHOTS}/start.png`, fullPage: true })
})

test('completes the full assessment and produces a shareable result', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: '开始检测' }).first().click()

  await expect(page).toHaveURL(/\/test\/hardware/)
  await page.screenshot({ path: `${SHOTS}/hardware.png`, fullPage: true })
  await page.getByRole('button', { name: '下一步' }).click()

  await expect(page).toHaveURL(/\/test\/quiz/)
  await page.screenshot({ path: `${SHOTS}/quiz.png`, fullPage: true })
  await completeQuiz(page)

  // --- interactive lab: CLI, software self-check, scenarios ---
  await expect(page).toHaveURL(/\/test\/lab/)
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
