import assert from 'node:assert/strict'
import test from 'node:test'

import { createMockProject } from '../../src/app/mock-data.ts'
import { deriveViewState } from '../../src/app/state.ts'
import { APP_VIEW_STATES } from '../../src/app/types.ts'

test('the kernel exposes exactly the six accepted states', () => {
  assert.deepEqual(APP_VIEW_STATES, [
    'empty',
    'loaded',
    'trim-on',
    'trim-off',
    'speed-on',
    'playing',
  ])
})

test('one view derives all six states in precedence order', () => {
  const loaded = createMockProject()
  const trimOn = createMockProject({ trim_assist_on: true })
  const speedOn = createMockProject({
    trim_assist_on: true,
    speed_assist_on: true,
  })

  assert.equal(
    deriveViewState({ project: null, playing: false, trimWasReverted: false }),
    'empty',
  )
  assert.equal(
    deriveViewState({ project: loaded, playing: false, trimWasReverted: false }),
    'loaded',
  )
  assert.equal(
    deriveViewState({ project: trimOn, playing: false, trimWasReverted: false }),
    'trim-on',
  )
  assert.equal(
    deriveViewState({ project: loaded, playing: false, trimWasReverted: true }),
    'trim-off',
  )
  assert.equal(
    deriveViewState({ project: speedOn, playing: false, trimWasReverted: false }),
    'speed-on',
  )
  assert.equal(
    deriveViewState({ project: speedOn, playing: true, trimWasReverted: false }),
    'playing',
  )
})

test('playing outranks assist lamps and speed outranks trim', () => {
  const both = createMockProject({
    trim_assist_on: true,
    speed_assist_on: true,
  })
  assert.equal(
    deriveViewState({ project: both, playing: false, trimWasReverted: true }),
    'speed-on',
  )
  assert.equal(
    deriveViewState({ project: both, playing: true, trimWasReverted: true }),
    'playing',
  )
})
