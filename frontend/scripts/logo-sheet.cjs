/* Renders a labelled contact sheet of every candidate logo for eyeballing. */
const fs = require('fs')
const { chromium } = require('playwright')

;(async () => {
  const res = await fetch('http://127.0.0.1:5000/api/catalog')
  const { candidates } = await res.json()
  const logos = {}
  const src = fs.readFileSync('src/assets/logos.ts', 'utf8')
  const re = /"([a-z0-9-]+)": \{"title":"([^"]*)","hex":"([^"]*)","path":"([^"]*)"\}/g
  let m
  while ((m = re.exec(src))) logos[m[1]] = { title: m[2], hex: m[3], path: m[4] }

  const cells = candidates.map((c) => {
    const l = logos[c.id]
    const glyph = l
      ? `<svg width="40" height="40" viewBox="0 0 24 24"><path d="${l.path}" fill="#fff"/></svg>`
      : `<span style="font:600 20px sans-serif;color:#fff">${c.monogram || '•'}</span>`
    return `<figure style="margin:0;text-align:center">
      <div style="width:64px;height:64px;background:${c.color};display:flex;align-items:center;justify-content:center;border-radius:10px">${glyph}</div>
      <figcaption style="font:11px/1.3 sans-serif;margin-top:4px">${c.name}</figcaption>
      <figcaption style="font:10px sans-serif;color:#888">${l ? 'logo' : 'fallback'}</figcaption>
    </figure>`
  }).join('')

  const html = `<html><body style="background:#fff;padding:16px">
    <div style="display:grid;grid-template-columns:repeat(9,1fr);gap:12px">${cells}</div>
  </body></html>`

  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1100, height: 900 } })
  await page.setContent(html)
  await page.screenshot({ path: '/tmp/logo-sheet.png', fullPage: true })
  await browser.close()
  console.log('logos:', Object.keys(logos).length, 'candidates:', candidates.length)
})()
