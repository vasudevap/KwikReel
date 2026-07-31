import {
  createElement,
  type ButtonHTMLAttributes,
  type CSSProperties,
  type ReactNode,
} from 'react'

import {
  counterSlots,
  middleTruncate,
  nameForSurface,
  type CounterKind,
  type NameSurface,
} from './tokens.ts'

function classes(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ')
}

export interface ScrewProps {
  className?: string
}

export function Screw({ className }: ScrewProps = {}) {
  return createElement('span', {
    'aria-hidden': true,
    className: classes('kr-screw', className),
  })
}

export interface RackEarProps {
  side: 'left' | 'right'
}

export function RackEar({ side }: RackEarProps) {
  return createElement(
    'span',
    { 'aria-hidden': true, className: classes('kr-ear', `kr-ear--${side}`) },
    createElement(Screw),
    createElement(Screw),
  )
}

export interface RackModuleProps {
  label: string
  children?: ReactNode
  className?: string
}

export function RackModule({ label, children, className }: RackModuleProps) {
  return createElement(
    'section',
    { className: classes('kr-module', className), 'aria-label': label },
    createElement(RackEar, { side: 'left' }),
    createElement(
      'div',
      { className: 'kr-module__inside' },
      createElement(
        'header',
        { className: 'kr-module__header' },
        createElement('span', { className: 'kr-module__plate' }, label),
      ),
      createElement('div', { className: 'kr-module__body' }, children),
    ),
    createElement(RackEar, { side: 'right' }),
  )
}

export type LampState = 'off' | 'active' | 'attention'

export interface LampProps {
  state?: LampState
  small?: boolean
  label?: string
}

export function Lamp({ state = 'off', small = false, label }: LampProps) {
  return createElement('span', {
    'aria-label': label,
    'aria-hidden': label ? undefined : true,
    className: classes(
      'kr-lamp',
      small && 'kr-lamp--small',
      state !== 'off' && `kr-lamp--${state}`,
    ),
    role: label ? 'img' : undefined,
  })
}

export const GLYPHS = Object.freeze([
  'bin',
  'link',
  'speaker',
  'reject',
  'rerun',
  'pencil',
  'play',
  'pause',
  'previous',
  'next',
  'step-back',
  'step-forward',
  'up',
  'down',
] as const)

export type GlyphName = (typeof GLYPHS)[number]

export interface GlyphProps {
  name: GlyphName
}

export function Glyph({ name }: GlyphProps) {
  return createElement('span', {
    'aria-hidden': true,
    className: classes('kr-glyph', `kr-glyph--${name}`),
  })
}

type NativeButtonProps = Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  'children' | 'className' | 'disabled'
>

export interface PhysicalKeyProps extends NativeButtonProps {
  label: string
  glyph?: GlyphName
  lamp?: LampState
  ring?: Exclude<LampState, 'off'> | 'none'
  pressed?: boolean
  compact?: boolean
  className?: string
}

export function PhysicalKey({
  label,
  glyph,
  lamp,
  ring = 'none',
  pressed = false,
  compact = false,
  className,
  type = 'button',
  ...buttonProps
}: PhysicalKeyProps) {
  const content: ReactNode[] = []
  if (lamp) content.push(createElement(Lamp, { key: 'lamp', state: lamp, small: true }))
  if (glyph) {
    content.push(createElement(Glyph, { key: 'glyph', name: glyph }))
  } else {
    content.push(label)
  }

  return createElement(
    'button',
    {
      ...buttonProps,
      'aria-label': glyph ? label : buttonProps['aria-label'],
      'aria-pressed': pressed,
      className: classes(
        'kr-key',
        glyph && 'kr-key--icon',
        compact && 'kr-key--compact',
        lamp && 'kr-key--lamp',
        ring !== 'none' && `kr-key--ring-${ring}`,
        pressed && 'kr-key--pressed',
        className,
      ),
      type,
    },
    ...content,
  )
}

type RackStyle = CSSProperties & {
  '--kr-counter-slots'?: number
}

export interface SevenSegmentProps {
  value: string
  kind?: CounterKind
  slots?: number
  ghost?: string
  small?: boolean
  label: string
}

function counterGhost(value: string, slots: number): string {
  const replaced = value.replace(/[0-9A-Z#]/g, '8')
  return replaced.padStart(slots, '8')
}

export function SevenSegment({
  value,
  kind = 'time',
  slots = counterSlots(kind),
  ghost,
  small = false,
  label,
}: SevenSegmentProps) {
  const style: RackStyle = { '--kr-counter-slots': slots }
  return createElement(
    'span',
    {
      'aria-label': `${label}: ${value || 'not set'}`,
      className: classes('kr-segment', small && 'kr-segment--small'),
      role: 'status',
      style,
    },
    createElement(
      'span',
      { 'aria-hidden': true, className: 'kr-segment__ghost' },
      ghost ?? counterGhost(value, slots),
    ),
    value
      ? createElement('span', { className: 'kr-segment__value' }, value)
      : null,
  )
}

export interface GlassProps {
  children?: ReactNode
  className?: string
  label?: string
  variant?: 'lcd' | 'vfd'
}

export function Glass({
  children,
  className,
  label,
  variant = 'lcd',
}: GlassProps) {
  return createElement(
    'div',
    {
      'aria-label': label,
      className: classes('kr-glass', `kr-glass--${variant}`, className),
    },
    children,
  )
}

export interface NameGlassProps {
  value: string
  surface: NameSurface
  className?: string
  label?: string
}

export function NameGlass({
  value,
  surface,
  className,
  label = 'Name',
}: NameGlassProps) {
  return createElement(
    Glass,
    { className: classes('kr-name-glass', className), label, variant: 'vfd' },
    createElement(
      'span',
      { className: 'kr-name-glass__value', title: value },
      nameForSurface(value, surface),
    ),
  )
}

export interface LabeledHousingProps {
  label: string
  children?: ReactNode
  locked?: boolean
  className?: string
}

export function LabeledHousing({
  label,
  children,
  locked = false,
  className,
}: LabeledHousingProps) {
  return createElement(
    'span',
    {
      className: classes(
        'kr-housing',
        locked && 'kr-housing--locked',
        className,
      ),
    },
    createElement('span', { className: 'kr-housing__label' }, label),
    createElement('span', { className: 'kr-housing__body' }, children),
  )
}

export interface FixedNameProps {
  value: string
  budget: number
  className?: string
}

export function FixedName({ value, budget, className }: FixedNameProps) {
  return createElement(
    'span',
    { className: classes('kr-fixed-name', className), title: value },
    middleTruncate(value, budget),
  )
}

export interface RackColumnsProps {
  monitor: ReactNode
  instruments: ReactNode
}

export function RackColumns({ monitor, instruments }: RackColumnsProps) {
  return createElement(
    'div',
    { className: 'kr-columns' },
    createElement('div', { className: 'kr-columns__monitor' }, monitor),
    createElement('div', { className: 'kr-columns__instruments' }, instruments),
  )
}

export interface RackFrameProps {
  children?: ReactNode
  local?: boolean
  brand?: string
  className?: string
}

export function RackFrame({
  children,
  local = true,
  brand = 'KwikReel',
  className,
}: RackFrameProps) {
  return createElement(
    'div',
    { className: classes('kr-rig', className) },
    createElement(
      'div',
      { className: 'kr-wall' },
      createElement(
        'div',
        { className: 'kr-hud' },
        createElement(
          'span',
          { className: classes('kr-hud__local', local && 'kr-hud__local--on') },
          createElement('i', { 'aria-hidden': true }),
          'LOCAL',
        ),
        createElement('span', { className: 'kr-grow' }),
        createElement('span', { className: 'kr-brandplate' }, brand),
      ),
      createElement('main', { className: 'kr-rack' }, children),
    ),
    createElement('div', { 'aria-hidden': true, className: 'kr-bench' }),
  )
}
