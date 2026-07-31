import { Monitor, Transport } from './components.ts'
import './monitor.css'

import type { SlotProvider } from '../app/types.ts'

export default {
  monitor: Monitor,
  transport: Transport,
} satisfies SlotProvider
