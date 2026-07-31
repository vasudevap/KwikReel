import assert from 'node:assert/strict'
import test from 'node:test'

import {
  COUNTER_SLOTS,
  NAME_BUDGETS,
  RACK_GEOMETRY,
  counterSlots,
  middleTruncate,
  nameForSurface,
} from '../../src/rack/tokens.ts'

test('v3z geometry causes are frozen at their accepted values', () => {
  assert.deepEqual(RACK_GEOMETRY, {
    minWidthPx: 960,
    measuredHeightPx: 767,
    monitorColumnPx: 465,
    sideColumnMinPx: 470,
    columnGapPx: 3,
    chromePx: 20,
    moduleGapPx: 3,
    moduleEarPx: 21,
    screwPx: 8,
    iconKeyPx: 26,
    indexRows: 4,
    indexRowPitchPx: 33,
    indexGlassPx: 138,
    logGlassPx: 65,
    lockedHousingPx: 232,
  })
})

test('every name surface has a fixed middle-truncation budget', () => {
  assert.deepEqual(NAME_BUDGETS, {
    reel: 18,
    monitor: 30,
    track: 28,
    editor: 24,
    index: 24,
  })

  const longName = 'Sunday at Hanlan’s Point — family cut'
  for (const [surface, budget] of Object.entries(NAME_BUDGETS)) {
    const rendered = nameForSurface(longName, surface)
    assert.equal(rendered.length, budget)
    assert.match(rendered, /…/)
    assert.ok(longName.startsWith(rendered.split('…')[0]))
    assert.ok(longName.endsWith(rendered.split('…')[1]))
  }
})

test('middle truncation preserves short names and rejects unsafe budgets', () => {
  assert.equal(middleTruncate('Family', 18), 'Family')
  assert.equal(middleTruncate('ABCDEFGHIJK', 7), 'ABC…IJK')
  assert.throws(() => middleTruncate('Family', 4), RangeError)
  assert.throws(() => middleTruncate('Family', 5.5), RangeError)
})

test('counter kinds reserve stable character slots', () => {
  assert.deepEqual(COUNTER_SLOTS, {
    time: 5,
    rate: 4,
    queue: 9,
    windowRange: 11,
    resolution: 5,
  })
  for (const [kind, slots] of Object.entries(COUNTER_SLOTS)) {
    assert.equal(counterSlots(kind), slots)
  }
})
