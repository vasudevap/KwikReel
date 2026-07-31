import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import { GLYPHS } from '../../src/rack/primitives.ts'

const cssUrl = new URL('../../src/rack/rack.css', import.meta.url)
const css = await readFile(cssUrl, 'utf8')

test('CSS encodes the fixed v3z rack geometry without responsive reflow', () => {
  assert.match(css, /\.kr-rig\s*\{[^}]*min-width:\s*960px/s)
  assert.match(css, /\.kr-columns__monitor\s*\{[^}]*width:\s*465px/s)
  assert.match(css, /inset:\s*0 0 auto 468px/)
  assert.match(css, /\.kr-key--icon\s*\{[^}]*width:\s*26px/s)
  assert.match(css, /\.kr-housing--locked\s*\{[^}]*width:\s*232px/s)
  assert.doesNotMatch(css, /@media/)
})

test('all accepted control glyphs are implemented in CSS', () => {
  for (const glyph of GLYPHS) {
    assert.match(css, new RegExp(`\\.kr-glyph--${glyph}(?:::|\\s|,)`))
  }
})

test('all fonts are embedded and require no network request', async () => {
  const names = ['barlow.css', 'plexmono.css', 'dseg7.css', 'dseg14.css']
  for (const name of names) {
    const source = await readFile(new URL(`../../src/rack/fonts/${name}`, import.meta.url), 'utf8')
    assert.match(source, /data:font\/woff2;base64,/)
    assert.doesNotMatch(source, /https?:\/\//)
  }
  assert.match(css, /'Barlow Semi Condensed'/)
  assert.match(css, /'DSEG7 Classic'/)
  assert.match(css, /'IBM Plex Mono'/)
})
