import assert from 'node:assert/strict'
import test from 'node:test'

import { MockClient } from '../../src/app/mock-client.ts'
import { createMockProject } from '../../src/app/mock-data.ts'
import { OptimisticProjectQueue } from '../../src/app/optimistic-queue.ts'
import { projectPatchOperation } from '../../src/app/operations.ts'

function harness(client, project) {
  const projects = []
  const logs = []
  const pending = []
  const queue = new OptimisticProjectQueue({
    client,
    project,
    now: () => '2026-07-30T15:00:00Z',
    onProject(next, count) {
      projects.push(next)
      pending.push(count)
    },
    onLog(entry) {
      logs.push(entry)
    },
  })
  return { logs, pending, projects, queue }
}

test('queued writes apply instantly and commit in strict order', async () => {
  const project = createMockProject()
  const client = new MockClient({ project })
  const { pending, projects, queue } = harness(client, project)

  const rename = queue.enqueue(projectPatchOperation({ name: 'Queued name' }))
  const retarget = queue.enqueue(
    projectPatchOperation({ target_duration_s: 42 }),
  )

  assert.equal(projects.at(-1).name, 'Queued name')
  assert.equal(projects.at(-1).target_duration_s, 42)
  assert.equal(pending.at(-1), 2)

  const [renameResult, targetResult] = await Promise.all([rename, retarget])
  assert.equal(renameResult.ok, true)
  assert.equal(targetResult.ok, true)
  assert.deepEqual(
    client.calls.filter((call) => call === 'patchProject'),
    ['patchProject', 'patchProject'],
  )
  assert.equal(projects.at(-1).name, 'Queued name')
  assert.equal(projects.at(-1).target_duration_s, 42)
  assert.equal(pending.at(-1), 0)
})

test('a 409 reverts only the failed edit and rebases later queued intent', async () => {
  const project = createMockProject()
  const client = new MockClient({ project })
  client.conflictNextWrite()
  const { logs, projects, queue } = harness(client, project)

  const staleRename = queue.enqueue(
    projectPatchOperation({ name: 'Must revert' }),
  )
  const laterTarget = queue.enqueue(
    projectPatchOperation({ target_duration_s: 54 }),
  )

  assert.equal(projects.at(-1).name, 'Must revert')
  assert.equal(projects.at(-1).target_duration_s, 54)

  const [renameResult, targetResult] = await Promise.all([
    staleRename,
    laterTarget,
  ])
  assert.equal(renameResult.ok, false)
  assert.equal(targetResult.ok, true)
  assert.equal(projects.at(-1).name, project.name)
  assert.equal(projects.at(-1).target_duration_s, 54)
  assert.equal(logs.length, 1)
  assert.equal(logs[0].code, 'SAVE_CONFLICT')
  assert.match(logs[0].text, /reverted/)
  assert.ok(client.calls.includes('getProject'))
  assert.ok(client.calls.includes('appendClientLog'))
})

test('a failed save is visible even when persistence must be retried', async () => {
  const project = createMockProject()
  class OfflineClient extends MockClient {
    async patchProject() {
      throw new Error('offline')
    }

    async appendClientLog() {
      throw new Error('offline')
    }
  }
  const client = new OfflineClient({ project })
  const { logs, projects, queue } = harness(client, project)

  const result = await queue.enqueue(
    projectPatchOperation({ output_resolution: '720p' }),
  )
  assert.equal(result.ok, false)
  assert.equal(projects.at(-1).output_resolution, project.output_resolution)
  assert.equal(logs[0].code, 'SAVE_FAILED')
  assert.match(logs[0].text, /reverted/)
})
