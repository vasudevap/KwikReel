import assert from 'node:assert/strict'
import test from 'node:test'

import { createMockProject } from '../../src/app/mock-data.ts'
import {
  buildPlaybackQueue,
  effectiveTrim,
  formatClock,
  playbackRateAt,
  recordedResolution,
} from '../../src/monitor/timeline.ts'

test('the playback queue follows the ephemeral lit set in project order', () => {
  const project = createMockProject()
  project.sources[0].path = 'mock-media/beach-walk.mp4'
  project.sources[1].path = 'mock-media/wave-jump.mp4'
  const queue = buildPlaybackQueue(
    project,
    ['source-b', 'source-a'],
    (sourceId) => `/api/media/proxy/${sourceId}`,
  )

  assert.deepEqual(queue.map((item) => item.sourceId), ['source-b', 'source-a'])
  assert.equal(queue[0].proxyUrl, '/api/media/proxy/source-b')
})

test('effective trim and speed are derived rather than read from user fields', () => {
  const project = createMockProject({ trim_assist_on: true, speed_assist_on: true })
  const source = project.sources[0]
  const clip = project.clips[0]
  const trim = effectiveTrim(project, clip, source)
  const [item] = buildPlaybackQueue(project, ['source-a'], () => '/proxy')

  assert.deepEqual(trim, clip.proposals.segments.value)
  assert.equal(playbackRateAt(item, 2.5), 1.5)
  assert.equal(playbackRateAt(item, 6), 1)
})

test('trimmed-out, damaged and proxy-less clips never enter playback', () => {
  const project = createMockProject()
  project.clips[0].origin.segments = 'user'
  project.clips[0].segment = { in_s: 2, out_s: 2 }
  project.sources[1].readable = false
  const queue = buildPlaybackQueue(project, ['source-a', 'source-b'], () => '/proxy')
  assert.deepEqual(queue, [])
})

test('transport readouts and recorded format stay deterministic', () => {
  const project = createMockProject()
  const [item] = buildPlaybackQueue(project, ['source-a'], () => '/proxy')
  assert.equal(formatClock(64.9), '1:04')
  assert.equal(recordedResolution(item), '1080P')
})
