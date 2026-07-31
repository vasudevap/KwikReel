import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import { AppController } from '../../src/app/controller.ts'
import { MockClient } from '../../src/app/mock-client.ts'
import { mockSnapshotForView } from '../../src/app/mock-data.ts'
import { resolveSlots } from '../../src/app/registry.ts'
import { AppShell } from '../../src/app/shell.ts'
import { APP_VIEW_STATES } from '../../src/app/types.ts'

function renderView(view, slots = resolveSlots([])) {
  const snapshot = mockSnapshotForView(view)
  const client = new MockClient({
    log: [...snapshot.log],
    project: snapshot.project,
  })
  const controller = new AppController(client, snapshot)
  return renderToStaticMarkup(
    h(AppShell, {
      actions: controller,
      client,
      slots,
      snapshot,
    }),
  )
}

test('all six states render as the same one-view slot topology', () => {
  for (const view of APP_VIEW_STATES) {
    const markup = renderView(view)
    assert.match(markup, new RegExp(`data-app-state="${view}"`))
    assert.match(markup, /data-slot="hud"/)
    for (const name of [
      'monitor',
      'reel',
      'transport',
      'sound',
      'editor',
      'index',
      'log',
    ]) {
      assert.match(markup, new RegExp(`kr-app__slot--${name}`))
    }
    assert.match(markup, /Honest placeholder/)
    assert.doesNotMatch(markup, /\sdisabled(?:=|>|\s)/)
  }
})

test('future lanes replace typed slots without changing the shell', () => {
  function Monitor() {
    return h('section', { 'data-real-slot': 'monitor' }, 'Monitor lane')
  }
  const slots = resolveSlots([{ monitor: Monitor }])
  const markup = renderView('loaded', slots)
  assert.match(markup, /data-real-slot="monitor"/)
  assert.doesNotMatch(markup, /kr-app__slot--monitor/)
  assert.match(markup, /kr-app__slot--transport/)
})

test('two lanes cannot claim the same slot silently', () => {
  function One() {
    return null
  }
  function Two() {
    return null
  }
  assert.throws(
    () => resolveSlots([{ sound: One }, { sound: Two }]),
    /more than one frontend lane claims the sound slot/,
  )
})
