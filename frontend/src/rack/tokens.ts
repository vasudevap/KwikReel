/**
 * WO-125 · Frozen v3z rack tokens.
 *
 * These values encode the causes behind SPEC.md §10.1's stable geometry. Later
 * frontend lanes consume them; they do not rediscover their own key sizes,
 * window counts, name budgets, or counter widths.
 */

export const RACK_GEOMETRY = Object.freeze({
  minWidthPx: 960,
  measuredHeightPx: 767,
  monitorColumnPx: 465,
  sideColumnMinPx: 470,
  columnGapPx: 3,
  chromePx: 20,
  moduleGapPx: 3,
  moduleEarPx: 21,
  screwPx: 8,
  iconKeyPx: 26,
  indexRows: 4,
  indexRowPitchPx: 33,
  indexGlassPx: 138,
  logGlassPx: 65,
  lockedHousingPx: 232,
})

export const RACK_COLOURS = Object.freeze({
  panelTop: '#212226',
  panelBottom: '#17181b',
  glass: '#05130c',
  counter: '#ffc42e',
  glassText: '#63f7a4',
  active: '#34d37e',
  attention: '#ffc02e',
  proposal: '#ffa53a',
  fault: '#ff6a5e',
  steelText: '#c9ccd1',
  steelSubtle: '#7d8189',
})

export const NAME_BUDGETS = Object.freeze({
  reel: 18,
  monitor: 30,
  track: 28,
  editor: 24,
  index: 24,
})

export type NameSurface = keyof typeof NAME_BUDGETS

export const COUNTER_SLOTS = Object.freeze({
  time: 5,
  rate: 4,
  queue: 9,
  windowRange: 11,
  resolution: 5,
})

export type CounterKind = keyof typeof COUNTER_SLOTS

export function middleTruncate(value: string, budget: number): string {
  if (!Number.isInteger(budget) || budget < 5) {
    throw new RangeError('a name budget must be an integer of at least 5')
  }
  if (value.length <= budget) return value

  const visible = budget - 1
  const head = Math.ceil(visible / 2)
  const tail = Math.floor(visible / 2)
  return `${value.slice(0, head)}…${value.slice(-tail)}`
}

export function nameForSurface(value: string, surface: NameSurface): string {
  return middleTruncate(value, NAME_BUDGETS[surface])
}

export function counterSlots(kind: CounterKind): number {
  return COUNTER_SLOTS[kind]
}
