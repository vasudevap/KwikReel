import { createElement } from 'react'

import { Glass, RackModule } from '../rack/primitives.ts'
import type {
  AppModuleProps,
  ModuleComponent,
  ModuleSlotName,
  ModuleSlots,
} from './types.ts'

const SLOT_WORK_ORDERS: Record<ModuleSlotName, string> = {
  hud: 'WO-132',
  monitor: 'WO-127',
  reel: 'WO-132',
  transport: 'WO-127',
  sound: 'WO-128',
  editor: 'WO-130',
  index: 'WO-129',
  log: 'WO-131',
}

function labelFor(name: ModuleSlotName): string {
  if (name === 'index') return 'Clip index'
  return name[0].toUpperCase() + name.slice(1)
}

function HudPlaceholder({ snapshot }: AppModuleProps) {
  return createElement(
    'div',
    { className: 'kr-hud kr-app__hud', 'data-slot': 'hud' },
    createElement(
      'span',
      { className: 'kr-hud__local kr-hud__local--on' },
      createElement('i', { 'aria-hidden': true }),
      'LOCAL',
    ),
    createElement(
      'span',
      { className: 'kr-app__hud-note' },
      `HUD placeholder · ${snapshot.view} · ${SLOT_WORK_ORDERS.hud}`,
    ),
    createElement('span', { className: 'kr-grow' }),
    createElement('span', { className: 'kr-brandplate' }, 'KwikReel'),
  )
}

function PlaceholderGlass({
  name,
  snapshot,
}: AppModuleProps & { name: ModuleSlotName }) {
  if (name === 'log') {
    const entries = [...snapshot.log].reverse().slice(0, 3)
    return createElement(
      Glass,
      {
        className: 'kr-app__placeholder-glass kr-app__placeholder-log',
        label: 'Temporary Log view',
        variant: 'vfd',
      },
      ...(entries.length
        ? entries.map((entry) =>
            createElement(
              'div',
              { className: `kr-app__log-line kr-app__log-line--${entry.kind}`, key: entry.at + entry.text },
              createElement('span', null, entry.kind === 'info' ? '·' : entry.kind.toUpperCase()),
              createElement('span', null, entry.text),
            ),
          )
        : [
            createElement(
              'span',
              { key: 'empty' },
              `Persistent Log surface awaiting ${SLOT_WORK_ORDERS.log}`,
            ),
          ]),
    )
  }

  return createElement(
    Glass,
    {
      className: 'kr-app__placeholder-glass',
      label: `${labelFor(name)} placeholder`,
      variant: name === 'monitor' ? 'lcd' : 'vfd',
    },
    createElement('span', { className: 'kr-app__placeholder-title' }, labelFor(name)),
    createElement(
      'span',
      { className: 'kr-app__placeholder-copy' },
      `Honest placeholder · ${SLOT_WORK_ORDERS[name]}`,
    ),
    createElement(
      'span',
      { className: 'kr-app__placeholder-state' },
      `view ${snapshot.view}`,
    ),
  )
}

function makePlaceholder(name: Exclude<ModuleSlotName, 'hud'>): ModuleComponent {
  return function PlaceholderModule(props: AppModuleProps) {
    return createElement(
      RackModule,
      {
        className: `kr-app__slot kr-app__slot--${name}`,
        label: labelFor(name),
      },
      createElement(PlaceholderGlass, { ...props, name }),
    )
  }
}

export const PLACEHOLDER_SLOTS: ModuleSlots = Object.freeze({
  hud: HudPlaceholder,
  monitor: makePlaceholder('monitor'),
  reel: makePlaceholder('reel'),
  transport: makePlaceholder('transport'),
  sound: makePlaceholder('sound'),
  editor: makePlaceholder('editor'),
  index: makePlaceholder('index'),
  log: makePlaceholder('log'),
})
