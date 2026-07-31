import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const components = await readFile(
  new URL('../../src/monitor/components.ts', import.meta.url),
  'utf8',
)
const playback = await readFile(
  new URL('../../src/monitor/playback-store.ts', import.meta.url),
  'utf8',
)
const slot = await readFile(
  new URL('../../src/monitor/slot.ts', import.meta.url),
  'utf8',
)
const css = await readFile(
  new URL('../../src/monitor/monitor.css', import.meta.url),
  'utf8',
)

test('one provider claims exactly Monitor and Transport', () => {
  assert.match(slot, /monitor:\s*Monitor/)
  assert.match(slot, /transport:\s*Transport/)
  assert.doesNotMatch(slot, /sound:|editor:|index:|log:|reel:|hud:/)
})

test('the Monitor uses the measured dual-video strategy', () => {
  assert.match(components, /\(\[0, 1\] as const\)\.map/)
  assert.match(components, /data-dual-video/)
  assert.match(components, /handleLoaded/)
  assert.match(playback, /prepareVisibleSlots/)
})

test('the reel clock uses media events and no throttled scheduler', () => {
  assert.match(components, /onTimeUpdate/)
  assert.match(components, /data-clock-source': 'media-events'/)
  assert.doesNotMatch(playback + components, /requestAnimationFrame|requestVideoFrameCallback|setInterval|setTimeout/)
})

test('Transport keeps fixed controls, target, scrub and output selection', () => {
  for (const control of [
    'Previous queued clip',
    'Step back one frame',
    'Step forward one frame',
    'Next queued clip',
    'Loop',
    'Target',
    'Clip scrub position',
    '720p',
    '1080p',
    '4k',
  ]) {
    assert.match(components.toLowerCase(), new RegExp(control.toLowerCase()))
  }
  assert.match(css, /\.kr-monitor__screen\s*\{[^}]*width:\s*338px;[^}]*height:\s*600px;/s)
  assert.doesNotMatch(css, /@media/)
})
