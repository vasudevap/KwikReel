import { createElement } from 'react'
import { createRoot } from 'react-dom/client'

import { AppController } from './app/controller.ts'
import { createLiveClient } from './app/client.ts'
import { MockClient } from './app/mock-client.ts'
import { mockSnapshotForView } from './app/mock-data.ts'
import { resolveSlots } from './app/registry.ts'
import { AppRoot } from './app/root.ts'
import {
  APP_VIEW_STATES,
  type AppViewState,
  type SlotProvider,
} from './app/types.ts'
import './rack/rack.css'
import './app/app.css'

const discovered = import.meta.glob<SlotProvider>(
  [
    './monitor/slot.ts',
    './sound/slot.ts',
    './index/slot.ts',
    './editor/slot.ts',
    './log/slot.ts',
    './reel/slot.ts',
  ],
  { eager: true, import: 'default' },
)

function requestedMockView(): AppViewState {
  const requested = new URLSearchParams(globalThis.location.search).get('state')
  return APP_VIEW_STATES.includes(requested as AppViewState)
    ? (requested as AppViewState)
    : 'empty'
}

const token = (globalThis as { __REEL_TOKEN__?: string }).__REEL_TOKEN__
const initialSnapshot = mockSnapshotForView(requestedMockView())
const client = token
  ? createLiveClient({ capabilityToken: token })
  : new MockClient({
      log: [...initialSnapshot.log],
      project: initialSnapshot.project,
    })
const controller = new AppController(
  client,
  token ? mockSnapshotForView('empty') : initialSnapshot,
)
const slots = resolveSlots(Object.values(discovered))

if (token) {
  const projectId = new URLSearchParams(globalThis.location.search).get('project')
  if (projectId) {
    void controller.openProject(projectId).catch(() => {
      controller.appendFailure({
        kind: 'fault',
        text: 'Open failed: the local project could not be loaded.',
        code: 'PROJECT_OPEN_FAILED',
      })
    })
  }
}

createRoot(document.getElementById('root') as HTMLElement).render(
  createElement(AppRoot, { controller, slots }),
)
