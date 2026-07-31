import { createElement, useSyncExternalStore } from 'react'

import type { AppController } from './controller.ts'
import { AppShell } from './shell.ts'
import type { ModuleSlots } from './types.ts'

export interface AppRootProps {
  controller: AppController
  slots: ModuleSlots
}

export function AppRoot({ controller, slots }: AppRootProps) {
  const snapshot = useSyncExternalStore(
    controller.subscribe,
    controller.getSnapshot,
    controller.getSnapshot,
  )
  return createElement(AppShell, {
    actions: controller,
    client: controller.client,
    slots,
    snapshot,
  })
}
