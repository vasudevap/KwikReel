import {
  createElement,
  useEffect,
  useState,
  useSyncExternalStore,
  type ChangeEvent,
  type KeyboardEvent,
} from 'react'

import { PlaybackStore } from './playback-store.ts'
import {
  formatClock,
  recordedResolution,
  scrubPercent,
} from './timeline.ts'
import {
  Glyph,
  LabeledHousing,
  PhysicalKey,
  RackModule,
  SevenSegment,
} from '../rack/primitives.ts'
import type { AppModuleProps } from '../app/types.ts'

export const playbackStore = new PlaybackStore()

function usePlayback({ snapshot, client, actions }: AppModuleProps) {
  const playback = useSyncExternalStore(
    playbackStore.subscribe,
    playbackStore.getSnapshot,
  )
  useEffect(() => {
    playbackStore.configure(snapshot, client, actions)
  }, [snapshot, client, actions])
  return playback
}

export function Monitor(props: AppModuleProps) {
  const playback = usePlayback(props)
  const item = playback.queue[playback.activeIndex] ?? null
  const queueText = item
    ? `${item.name} · ${playback.activeIndex + 1} of ${playback.queue.length}${playback.playing ? '' : ' · cued'}`
    : ''

  return createElement(
    RackModule,
    {
      className: 'kr-app__slot kr-app__slot--monitor kr-monitor',
      label: 'Monitor',
    },
    createElement(
      'div',
      {
        className: 'kr-monitor__screen',
        'data-active-video': playback.activeSlot,
        'data-dual-video': 'true',
      },
      ...([0, 1] as const).map((slot) =>
        createElement('video', {
          'aria-label': `Preview deck ${slot === 0 ? 'A' : 'B'}`,
          className: `kr-monitor__video${playback.activeSlot === slot ? ' kr-monitor__video--active' : ''}`,
          key: slot,
          onEnded: () => playbackStore.handleEnded(slot),
          onLoadedData: () => playbackStore.handleLoaded(slot),
          onPlaying: () => playbackStore.handlePlaying(slot),
          onTimeUpdate: () => playbackStore.handleTimeUpdate(slot),
          playsInline: true,
          preload: 'auto',
          ref: (element: HTMLVideoElement | null) => playbackStore.attach(slot, element),
        }),
      ),
      item
        ? createElement('div', {
            'aria-hidden': true,
            className: `kr-monitor__synthetic kr-monitor__synthetic--${playback.activeIndex % 2}`,
          })
        : null,
      item
        ? createElement('span', { className: 'kr-monitor__queue', title: queueText }, queueText)
        : null,
      item
        ? createElement('span', { className: 'kr-monitor__resolution' }, recordedResolution(item))
        : null,
      item
        ? createElement(
            'button',
            {
              'aria-label': playback.playing ? 'Pause preview' : 'Play preview',
              className: 'kr-monitor__screen-toggle',
              onClick: () => playbackStore.togglePlaying(),
              type: 'button',
            },
            createElement(Glyph, { name: playback.playing ? 'pause' : 'play' }),
          )
        : createElement('div', { className: 'kr-monitor__empty' }, 'No tape loaded'),
    ),
  )
}

function targetParts(targetS: number): [string, string] {
  const safe = Math.max(0, Math.min(5999, Math.round(targetS)))
  return [
    String(Math.floor(safe / 60)).padStart(2, '0'),
    String(safe % 60).padStart(2, '0'),
  ]
}

function digits(value: string): string {
  return value.replace(/\D/g, '').slice(-2)
}

export function Transport(props: AppModuleProps) {
  const { snapshot, actions } = props
  const playback = usePlayback(props)
  const item = playback.queue[playback.activeIndex] ?? null
  const [initialMinutes, initialSeconds] = targetParts(
    snapshot.project?.target_duration_s ?? 75,
  )
  const [minutes, setMinutes] = useState(initialMinutes)
  const [seconds, setSeconds] = useState(initialSeconds)

  useEffect(() => {
    const [nextMinutes, nextSeconds] = targetParts(
      snapshot.project?.target_duration_s ?? 75,
    )
    setMinutes(nextMinutes)
    setSeconds(nextSeconds)
  }, [snapshot.project?.target_duration_s])

  const commitTarget = async () => {
    if (!snapshot.project) return
    const target = Number(minutes || 0) * 60 + Math.min(59, Number(seconds || 0))
    const outcome = await actions.patchProject({ target_duration_s: target })
    if (!outcome.ok) {
      const [oldMinutes, oldSeconds] = targetParts(
        outcome.project?.target_duration_s ?? snapshot.project.target_duration_s,
      )
      setMinutes(oldMinutes)
      setSeconds(oldSeconds)
    }
  }

  const commitOnEnter = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') event.currentTarget.blur()
  }

  const setTargetField = (
    setter: (value: string) => void,
    event: ChangeEvent<HTMLInputElement>,
  ) => setter(digits(event.currentTarget.value))

  const resolution = snapshot.project?.output_resolution ?? '1080p'
  const keepLeft = item ? (item.inS / item.durationS) * 100 : 0
  const keepWidth = item ? ((item.outS - item.inS) / item.durationS) * 100 : 0
  const cursor = scrubPercent(item, playback.currentTimeS)
  const step = item ? 1 / item.fps : 1 / 30

  return createElement(
    RackModule,
    {
      className: 'kr-app__slot kr-app__slot--transport kr-transport',
      label: 'Transport',
    },
    createElement(
      'div',
      { className: 'kr-transport__deck kr-transport__deck--controls' },
      createElement(PhysicalKey, {
        glyph: playback.playing ? 'pause' : 'play',
        label: playback.playing ? 'Pause preview' : 'Play preview',
        onClick: () => playbackStore.togglePlaying(),
      }),
      createElement(PhysicalKey, {
        glyph: 'previous',
        label: 'Previous queued clip',
        onClick: () => playbackStore.previous(),
      }),
      createElement(PhysicalKey, {
        glyph: 'step-back',
        label: 'Step back one frame',
        onClick: () => playbackStore.step(-1),
      }),
      createElement(PhysicalKey, {
        glyph: 'step-forward',
        label: 'Step forward one frame',
        onClick: () => playbackStore.step(1),
      }),
      createElement(PhysicalKey, {
        glyph: 'next',
        label: 'Next queued clip',
        onClick: () => playbackStore.next(),
      }),
      createElement(PhysicalKey, {
        className: 'kr-transport__loop',
        label: 'Loop',
        lamp: playback.loop ? 'active' : 'off',
        onClick: () => playbackStore.toggleLoop(),
        pressed: playback.loop,
      }),
      createElement(
        LabeledHousing,
        { className: 'kr-transport__target', label: 'Target', locked: true },
        createElement('input', {
          'aria-label': 'Target minutes',
          className: 'kr-transport__target-number',
          inputMode: 'numeric',
          onBlur: () => void commitTarget(),
          onChange: (event: ChangeEvent<HTMLInputElement>) => setTargetField(setMinutes, event),
          onKeyDown: commitOnEnter,
          value: minutes,
        }),
        createElement('span', { className: 'kr-transport__unit' }, 'min'),
        createElement('input', {
          'aria-label': 'Target seconds',
          className: 'kr-transport__target-number',
          inputMode: 'numeric',
          onBlur: () => void commitTarget(),
          onChange: (event: ChangeEvent<HTMLInputElement>) => setTargetField(setSeconds, event),
          onKeyDown: commitOnEnter,
          value: seconds,
        }),
        createElement('span', { className: 'kr-transport__unit' }, 'sec'),
      ),
    ),
    createElement(
      'div',
      { className: 'kr-transport__deck kr-transport__deck--scrub' },
      createElement(SevenSegment, {
        kind: 'time',
        label: 'Current clip time',
        small: true,
        value: item ? formatClock(playback.currentTimeS) : '',
      }),
      createElement(
        'div',
        {
          'aria-label': item
            ? `Clip scrub. In ${formatClock(item.inS)}, current ${formatClock(playback.currentTimeS)}, out ${formatClock(item.outS)}`
            : 'Clip scrub. No clip loaded.',
          className: 'kr-transport__scrub',
        },
        createElement('span', {
          'aria-hidden': true,
          className: 'kr-transport__keep',
          style: { left: `${keepLeft}%`, width: `${keepWidth}%` },
        }),
        createElement('span', {
          'aria-hidden': true,
          className: 'kr-transport__cursor',
          style: { left: `${cursor}%` },
        }),
        createElement('input', {
          'aria-label': 'Clip scrub position',
          className: 'kr-transport__scrub-input',
          max: item?.outS ?? 1,
          min: item?.inS ?? 0,
          onChange: (event: ChangeEvent<HTMLInputElement>) =>
            playbackStore.seekTo(Number(event.currentTarget.value)),
          step,
          type: 'range',
          value: item ? playback.currentTimeS : 0,
        }),
      ),
      createElement(SevenSegment, {
        kind: 'time',
        label: 'Clip out time',
        small: true,
        value: item ? formatClock(item.outS) : '',
      }),
      createElement(
        LabeledHousing,
        { className: 'kr-transport__output', label: 'Out', locked: true },
        createElement(
          'span',
          { className: 'kr-transport__resolutions' },
          ...(['720p', '1080p', '4k'] as const).map((value) =>
            createElement(PhysicalKey, {
              className: 'kr-transport__resolution-key',
              compact: true,
              key: value,
              label: value.toUpperCase(),
              lamp: resolution === value ? 'active' : 'off',
              onClick: () => void actions.patchProject({ output_resolution: value }),
              pressed: resolution === value,
            }),
          ),
        ),
      ),
    ),
    createElement('span', {
      'aria-hidden': true,
      'data-clock-source': 'media-events',
      'data-playback-strategy': 'dual-video-cross-swap',
      hidden: true,
    }),
  )
}
