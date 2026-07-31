import assert from 'node:assert/strict'
import test from 'node:test'

import { AppController } from '../../src/app/controller.ts'
import { MockClient } from '../../src/app/mock-client.ts'
import {
  createMockProject,
  mockSnapshotForView,
} from '../../src/app/mock-data.ts'
import { createSnapshot } from '../../src/app/state.ts'

test('the preview queue is session-only and defaults to project clip order', () => {
  const project = createMockProject({
    clips: [...createMockProject().clips].reverse(),
  })
  const snapshot = createSnapshot({ project })

  assert.deepEqual(snapshot.previewQueueSourceIds, ['source-a', 'source-b'])
  assert.equal('previewQueueSourceIds' in project, false)
})

test('the typed toggle removes and restores a clip in project order', () => {
  const initial = mockSnapshotForView('loaded')
  const controller = new AppController(
    new MockClient({ project: initial.project }),
    initial,
  )

  controller.togglePreviewQueue('source-a')
  assert.deepEqual(controller.getSnapshot().previewQueueSourceIds, ['source-b'])

  controller.togglePreviewQueue('source-a')
  assert.deepEqual(controller.getSnapshot().previewQueueSourceIds, [
    'source-a',
    'source-b',
  ])
})

test('empty and unknown queue actions cannot fabricate persisted state', () => {
  const empty = new AppController(new MockClient())
  empty.togglePreviewQueue('unknown')
  assert.deepEqual(empty.getSnapshot().previewQueueSourceIds, [])

  const initial = mockSnapshotForView('loaded')
  const before = JSON.stringify(initial.project)
  const controller = new AppController(
    new MockClient({ project: initial.project }),
    initial,
  )
  controller.togglePreviewQueue('unknown')
  assert.equal(JSON.stringify(controller.getSnapshot().project), before)
})
