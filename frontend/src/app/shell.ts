import { createElement } from 'react'

import { RackColumns } from '../rack/primitives.ts'
import type {
  AppActions,
  AppClient,
  AppSnapshot,
  ModuleSlots,
} from './types.ts'

export interface AppShellProps {
  snapshot: AppSnapshot
  client: AppClient
  actions: AppActions
  slots: ModuleSlots
}

export function AppShell({
  snapshot,
  client,
  actions,
  slots,
}: AppShellProps) {
  const moduleProps = { snapshot, client, actions }
  const monitor = createElement(slots.monitor, moduleProps)
  const instruments = createElement(
    'div',
    { className: 'kr-app__instruments' },
    createElement(slots.reel, moduleProps),
    createElement(slots.transport, moduleProps),
    createElement(slots.sound, moduleProps),
    createElement(slots.editor, moduleProps),
    createElement(slots.index, moduleProps),
    createElement(slots.log, moduleProps),
  )

  return createElement(
    'div',
    {
      className: 'kr-rig kr-app',
      'data-app-state': snapshot.view,
      'data-pending-writes': snapshot.pendingWrites,
    },
    createElement(
      'div',
      { className: 'kr-wall' },
      createElement(slots.hud, moduleProps),
      createElement(
        'main',
        { className: 'kr-rack' },
        createElement(RackColumns, { instruments, monitor }),
      ),
    ),
    createElement('div', { 'aria-hidden': true, className: 'kr-bench' }),
  )
}
