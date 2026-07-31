import { buildPlaybackQueue, playbackRateAt, type PlaybackItem } from './timeline.ts'
import type { AppActions, AppClient, AppSnapshot } from '../app/types.ts'

type Listener = () => void
type Slot = 0 | 1

export interface MediaElementLike {
  currentTime: number
  playbackRate: number
  readyState: number
  src: string
  load(): void
  pause(): void
  play(): Promise<void>
  removeAttribute?(name: string): void
}

export interface PlaybackSnapshot {
  queue: readonly PlaybackItem[]
  activeIndex: number
  currentTimeS: number
  loop: boolean
  playing: boolean
  activeSlot: Slot
}

interface PreparedSlot {
  item: PlaybackItem | null
  startAtS: number
}

const EMPTY_PLAYBACK: PlaybackSnapshot = Object.freeze({
  queue: Object.freeze([]),
  activeIndex: 0,
  currentTimeS: 0,
  loop: false,
  playing: false,
  activeSlot: 0,
})

export class PlaybackStore {
  private listeners = new Set<Listener>()
  private media: [MediaElementLike | null, MediaElementLike | null] = [null, null]
  private prepared: [PreparedSlot, PreparedSlot] = [
    { item: null, startAtS: 0 },
    { item: null, startAtS: 0 },
  ]
  private loadedSourceIds: [string | null, string | null] = [null, null]
  private actions: AppActions | null = null
  private snapshot: PlaybackSnapshot = EMPTY_PLAYBACK
  private autoPlaySlot: Slot | null = null

  getSnapshot = (): PlaybackSnapshot => this.snapshot

  subscribe = (listener: Listener): (() => void) => {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  configure(app: AppSnapshot, client: AppClient, actions: AppActions): void {
    this.actions = actions
    const queue = buildPlaybackQueue(
      app.project,
      app.previewQueueSourceIds,
      (sourceId) => client.proxyUrl(sourceId),
    )
    const currentId = this.snapshot.queue[this.snapshot.activeIndex]?.sourceId
    const retainedIndex = currentId
      ? queue.findIndex((item) => item.sourceId === currentId)
      : -1
    const activeIndex = retainedIndex >= 0 ? retainedIndex : 0
    const active = queue[activeIndex] ?? null
    const currentTimeS = active
      ? Math.max(active.inS, Math.min(this.snapshot.currentTimeS || active.inS, active.outS))
      : 0
    this.snapshot = Object.freeze({
      ...this.snapshot,
      queue,
      activeIndex,
      currentTimeS,
      playing: app.playing && queue.length > 0,
    })
    this.prepareVisibleSlots()
    this.emit()
  }

  attach(slot: Slot, element: MediaElementLike | null): void {
    this.media[slot] = element
    if (!element) this.loadedSourceIds[slot] = null
    if (element) this.prepareVisibleSlots()
  }

  toggleLoop(): void {
    this.update({ loop: !this.snapshot.loop })
  }

  togglePlaying(): void {
    if (this.snapshot.playing) this.pause()
    else void this.play()
  }

  pause(): void {
    this.media[this.snapshot.activeSlot]?.pause()
    this.actions?.setPlaying(false)
    this.update({ playing: false })
  }

  async play(): Promise<void> {
    const item = this.activeItem()
    if (!item) return
    const media = this.media[this.snapshot.activeSlot]
    if (!media || !item.proxyUrl) {
      this.actions?.setPlaying(true)
      this.update({ playing: true })
      return
    }
    if (media.readyState < 2) {
      this.autoPlaySlot = this.snapshot.activeSlot
      this.prepareSlot(this.snapshot.activeSlot, item, this.snapshot.currentTimeS)
      return
    }
    media.currentTime = this.snapshot.currentTimeS
    media.playbackRate = playbackRateAt(item, media.currentTime)
    try {
      await media.play()
    } catch {
      this.actions?.appendFailure({
        kind: 'fault',
        text: 'Preview failed: this proxy could not start playing.',
        code: 'PREVIEW_PLAY_FAILED',
        source_id: item.sourceId,
      })
      this.actions?.setPlaying(false)
      this.update({ playing: false })
    }
  }

  previous(): void {
    const length = this.snapshot.queue.length
    if (!length) return
    this.goTo(Math.max(0, this.snapshot.activeIndex - 1), this.snapshot.playing)
  }

  next(): void {
    const length = this.snapshot.queue.length
    if (!length) return
    const next = this.snapshot.activeIndex + 1
    if (next < length) this.goTo(next, this.snapshot.playing)
    else if (this.snapshot.loop) this.goTo(0, this.snapshot.playing)
    else this.pause()
  }

  step(direction: -1 | 1): void {
    const item = this.activeItem()
    if (!item) return
    this.pause()
    const frame = 1 / item.fps
    this.seekTo(this.snapshot.currentTimeS + direction * frame)
  }

  seekTo(sourceTimeS: number): void {
    const item = this.activeItem()
    if (!item) return
    const next = Math.max(item.inS, Math.min(sourceTimeS, item.outS))
    const media = this.media[this.snapshot.activeSlot]
    if (media) {
      media.currentTime = next
      media.playbackRate = playbackRateAt(item, next)
    }
    this.update({ currentTimeS: next })
  }

  handleLoaded(slot: Slot): void {
    const prepared = this.prepared[slot]
    const media = this.media[slot]
    if (!media || !prepared.item) return
    media.currentTime = prepared.startAtS
    media.playbackRate = playbackRateAt(prepared.item, prepared.startAtS)
    if (this.autoPlaySlot === slot) {
      this.autoPlaySlot = null
      void this.play()
    }
  }

  handlePlaying(slot: Slot): void {
    if (slot !== this.snapshot.activeSlot) return
    this.actions?.setPlaying(true)
    this.update({ playing: true })
  }

  handleTimeUpdate(slot: Slot): void {
    if (slot !== this.snapshot.activeSlot) return
    const item = this.activeItem()
    const media = this.media[slot]
    if (!item || !media) return
    const currentTimeS = media.currentTime
    if (currentTimeS >= item.outS - 1 / item.fps / 2) {
      this.next()
      return
    }
    const rate = playbackRateAt(item, currentTimeS)
    if (media.playbackRate !== rate) media.playbackRate = rate
    this.update({ currentTimeS })
  }

  handleEnded(slot: Slot): void {
    if (slot === this.snapshot.activeSlot) this.next()
  }

  private activeItem(): PlaybackItem | null {
    return this.snapshot.queue[this.snapshot.activeIndex] ?? null
  }

  private goTo(index: number, continuePlaying: boolean): void {
    const item = this.snapshot.queue[index]
    if (!item) return
    const oldSlot = this.snapshot.activeSlot
    const nextSlot: Slot = oldSlot === 0 ? 1 : 0
    this.media[oldSlot]?.pause()
    this.snapshot = Object.freeze({
      ...this.snapshot,
      activeIndex: index,
      activeSlot: nextSlot,
      currentTimeS: item.inS,
      playing: continuePlaying,
    })
    this.prepareVisibleSlots()
    this.emit()
    if (continuePlaying) void this.play()
  }

  private prepareVisibleSlots(): void {
    const active = this.activeItem()
    this.prepareSlot(this.snapshot.activeSlot, active, this.snapshot.currentTimeS)
    const nextIndex = this.snapshot.activeIndex + 1 < this.snapshot.queue.length
      ? this.snapshot.activeIndex + 1
      : this.snapshot.loop
        ? 0
        : -1
    const idleSlot: Slot = this.snapshot.activeSlot === 0 ? 1 : 0
    const next = nextIndex >= 0 ? this.snapshot.queue[nextIndex] : null
    this.prepareSlot(idleSlot, next ?? null, next?.inS ?? 0)
  }

  private prepareSlot(slot: Slot, item: PlaybackItem | null, startAtS: number): void {
    const media = this.media[slot]
    this.prepared[slot] = { item, startAtS }
    if (!media) return
    if (!item) {
      if (this.loadedSourceIds[slot] !== null) {
        media.pause()
        if (media.removeAttribute) media.removeAttribute('src')
        else media.src = ''
        media.load()
        this.loadedSourceIds[slot] = null
      }
      return
    }
    if (!item.proxyUrl) return
    if (this.loadedSourceIds[slot] !== item.sourceId) {
      this.loadedSourceIds[slot] = item.sourceId
      media.src = item.proxyUrl
      media.load()
      return
    }
    if (media.readyState >= 2) {
      media.currentTime = startAtS
      media.playbackRate = playbackRateAt(item, startAtS)
    }
  }

  private update(patch: Partial<PlaybackSnapshot>): void {
    this.snapshot = Object.freeze({ ...this.snapshot, ...patch })
    this.emit()
  }

  private emit(): void {
    for (const listener of this.listeners) listener()
  }
}
