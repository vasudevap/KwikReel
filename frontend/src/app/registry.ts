import { PLACEHOLDER_SLOTS } from './placeholders.ts'
import {
  MODULE_SLOT_NAMES,
  type ModuleSlots,
  type SlotProvider,
} from './types.ts'

export function resolveSlots(providers: readonly SlotProvider[]): ModuleSlots {
  const slots: ModuleSlots = { ...PLACEHOLDER_SLOTS }
  const claimed = new Set<string>()
  for (const provider of providers) {
    for (const name of MODULE_SLOT_NAMES) {
      const component = provider[name]
      if (!component) continue
      if (claimed.has(name)) {
        throw new Error(`more than one frontend lane claims the ${name} slot`)
      }
      slots[name] = component
      claimed.add(name)
    }
  }
  return slots
}
