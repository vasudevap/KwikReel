import assert from 'node:assert/strict'
import test from 'node:test'

import { AppController } from '../../src/app/controller.ts'
import { MockClient } from '../../src/app/mock-client.ts'
import { mockSnapshotForView } from '../../src/app/mock-data.ts'
import { PlaybackStore } from '../../src/monitor/playback-store.ts'

class FakeMedia {
  currentTime = 0
  playbackRate = 1
  readyState = 2
  src = ''
  loads = 0
  pauses = 0
  plays = 0

  load() {
    this.loads += 1
  }

  pause() {
    this.pauses += 1
  }

  async play() {
    this.plays += 1
  }
}

function harness() {
  const initial = mockSnapshotForView('loaded')
  for (const source of initial.project.sources) {
    source.path = `mock-media/${source.source_id}.mp4`
  }
  const client = new MockClient({ project: initial.project })
  const actions = new AppController(client, initial)
  const store = new PlaybackStore()
  store.configure(actions.getSnapshot(), client, actions)
  const a = new FakeMedia()
  const b = new FakeMedia()
  store.attach(0, a)
  store.attach(1, b)
  store.handleLoaded(0)
  store.handleLoaded(1)
  return { a, actions, b, store }
}

test('two media decks prepare the active clip and its successor', () => {
  const { a, b, store } = harness()
  assert.equal(a.src, '/api/media/proxy/source-a')
  assert.equal(b.src, '/api/media/proxy/source-b')
  assert.equal(store.getSnapshot().activeSlot, 0)
  assert.equal(store.getSnapshot().queue.length, 2)
})

test('the cut cross-swaps to the prepared idle deck', async () => {
  const { a, b, store } = harness()
  await store.play()
  store.handlePlaying(0)
  a.currentTime = store.getSnapshot().queue[0].outS
  store.handleTimeUpdate(0)
  await Promise.resolve()

  assert.equal(store.getSnapshot().activeIndex, 1)
  assert.equal(store.getSnapshot().activeSlot, 1)
  assert.equal(a.pauses > 0, true)
  assert.equal(b.plays, 1)
})

test('frame step pauses and clamps to the effective clip', () => {
  const { a, store } = harness()
  const item = store.getSnapshot().queue[0]
  store.seekTo(item.inS)
  store.step(-1)
  assert.equal(store.getSnapshot().currentTimeS, item.inS)
  store.step(1)
  assert.ok(Math.abs(store.getSnapshot().currentTimeS - (item.inS + 1 / item.fps)) < 1e-9)
  assert.equal(a.playbackRate, 1)
})

test('loop returns the queue to its prepared first clip', () => {
  const { store } = harness()
  store.toggleLoop()
  store.next()
  store.next()
  assert.equal(store.getSnapshot().activeIndex, 0)
  assert.equal(store.getSnapshot().loop, true)
})
