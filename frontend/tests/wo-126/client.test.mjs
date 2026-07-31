import assert from 'node:assert/strict'
import test from 'node:test'

import {
  ApiClientError,
  CLIENT_METHODS,
  LiveClient,
} from '../../src/app/client.ts'
import { MockClient } from '../../src/app/mock-client.ts'
import { createMockProject } from '../../src/app/mock-data.ts'

function response(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    async json() {
      return payload
    },
  }
}

test('mock and live clients implement the same frozen method surface', () => {
  const mock = new MockClient({ project: createMockProject() })
  const live = new LiveClient({
    capabilityToken: 'synthetic-token',
    fetch: async () => response(createMockProject()),
  })
  for (const method of CLIENT_METHODS) {
    assert.equal(typeof mock[method], 'function', `mock.${method}`)
    assert.equal(typeof live[method], 'function', `live.${method}`)
  }
})

test('live mutations carry the capability and optimistic version', async () => {
  const project = createMockProject()
  const calls = []
  const client = new LiveClient({
    baseUrl: 'http://127.0.0.1:5178',
    capabilityToken: 'synthetic-token',
    fetch: async (url, init) => {
      calls.push({ url, init })
      return response({ ...project, name: 'Renamed' })
    },
  })

  const saved = await client.patchProject(
    project.project_id,
    project.updated_at,
    { name: 'Renamed' },
  )
  assert.equal(saved.name, 'Renamed')
  assert.equal(calls.length, 1)
  assert.equal(
    calls[0].url,
    'http://127.0.0.1:5178/api/project/synthetic-project',
  )
  assert.equal(calls[0].init.method, 'PATCH')
  assert.equal(calls[0].init.headers['x-capability-token'], 'synthetic-token')
  assert.deepEqual(JSON.parse(calls[0].init.body), {
    updated_at: project.updated_at,
    name: 'Renamed',
  })
})

test('live reads stay same-origin shaped and do not send the capability', async () => {
  const project = createMockProject()
  let observed
  const client = new LiveClient({
    capabilityToken: 'synthetic-token',
    fetch: async (url, init) => {
      observed = { url, init }
      return response(project)
    },
  })
  await client.getProject(project.project_id)
  assert.equal(observed.url, '/api/project/synthetic-project')
  assert.equal(observed.init.method, 'GET')
  assert.equal(observed.init.headers['x-capability-token'], undefined)
})

test('the live client preserves a 409 as a typed conflict', async () => {
  const project = createMockProject()
  const client = new LiveClient({
    capabilityToken: 'synthetic-token',
    fetch: async () =>
      response(
        {
          error_code: 'conflict',
          human_text: 'The project changed since you loaded it.',
          remediation: 'Reload and try again.',
        },
        409,
      ),
  })
  await assert.rejects(
    () =>
      client.patchProject(project.project_id, project.updated_at, {
        name: 'Stale',
      }),
    (error) =>
      error instanceof ApiClientError &&
      error.isConflict &&
      error.envelope.error_code === 'conflict',
  )
})
