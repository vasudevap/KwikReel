import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import {
  GLYPHS,
  NameGlass,
  PhysicalKey,
  RackColumns,
  RackFrame,
  RackModule,
  SevenSegment,
} from '../../src/rack/primitives.ts'

test('rack modules always render two ears and four screws', () => {
  const markup = renderToStaticMarkup(
    h(RackModule, { label: 'Transport' }, h('span', null, 'body')),
  )
  assert.equal((markup.match(/kr-ear(?:\s|")/g) ?? []).length, 2)
  assert.equal((markup.match(/kr-screw/g) ?? []).length, 4)
  assert.match(markup, /kr-module__plate">Transport/)
})

test('every accepted glyph is CSS-drawn inside a present physical key', () => {
  for (const glyph of GLYPHS) {
    const markup = renderToStaticMarkup(
      h(PhysicalKey, { glyph, label: `Action ${glyph}` }),
    )
    assert.match(markup, /^<button/)
    assert.match(markup, new RegExp(`aria-label="Action ${glyph}"`))
    assert.match(markup, new RegExp(`kr-glyph--${glyph}`))
    assert.doesNotMatch(markup, /\sdisabled(?:=|>|\s)/)
    assert.doesNotMatch(markup, /[▶⏸⏮⏭✎↻🔗🗑]/u)
  }
})

test('key cap stays a key while lamps and rings carry state', () => {
  const markup = renderToStaticMarkup(
    h(PhysicalKey, {
      glyph: 'rerun',
      label: 'Rerun proposal',
      lamp: 'attention',
      ring: 'active',
    }),
  )
  assert.match(markup, /kr-key--lamp/)
  assert.match(markup, /kr-key--ring-active/)
  assert.match(markup, /kr-lamp--attention/)
})

test('seven-segment counters expose their value and reserve fixed slots', () => {
  const markup = renderToStaticMarkup(
    h(SevenSegment, { kind: 'time', label: 'Playhead', value: '02:14' }),
  )
  assert.match(markup, /aria-label="Playhead: 02:14"/)
  assert.match(markup, /--kr-counter-slots:5/)
  assert.match(markup, /kr-segment__ghost/)
  assert.match(markup, /kr-segment__value">02:14/)
})

test('name glass applies the surface budget but retains the full title', () => {
  const value = 'Sunday at Hanlan’s Point — family cut'
  const markup = renderToStaticMarkup(
    h(NameGlass, { surface: 'reel', value }),
  )
  assert.match(markup, new RegExp(`title="${value}"`))
  assert.match(markup, /Sunday at…mily cut/)
  assert.doesNotMatch(markup, new RegExp(`>${value}<`))
})

test('frame and columns preserve the fixed rack topology', () => {
  const markup = renderToStaticMarkup(
    h(
      RackFrame,
      null,
      h(RackColumns, {
        instruments: h('div', null, 'instruments'),
        monitor: h('div', null, 'monitor'),
      }),
    ),
  )
  assert.match(markup, /kr-hud__local--on/)
  assert.match(markup, /kr-columns__monitor/)
  assert.match(markup, /kr-columns__instruments/)
  assert.match(markup, /<main class="kr-rack"/)
})
