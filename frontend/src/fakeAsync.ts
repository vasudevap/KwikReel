// Simulated long-running jobs. ADR-008 rule 1: fake the REAL waiting times
// (~5 min analysis, ~5 min render) so the flow is DESIGNED against real latency
// — progress, minutes-remaining, and a "you can leave this screen" affordance.
// A demo-speed control lets the reviewer watch at real speed or fast-forward,
// instead of literally waiting five minutes on every pass. The real figure is
// always shown, so the 5-minute reality stays visible even when fast-forwarded.

export const REAL_JOB_SECONDS = 300 // the production reality we design against

export type DemoSpeed = 'real' | 'fast' | 'instant'

export interface DemoSpeedOption {
  id: DemoSpeed
  label: string
  wallSeconds: number
}

export const DEMO_SPEEDS: DemoSpeedOption[] = [
  { id: 'real', label: 'Real speed (~5 min)', wallSeconds: REAL_JOB_SECONDS },
  { id: 'fast', label: 'Fast-forward (~20 s)', wallSeconds: 20 },
  { id: 'instant', label: 'Skip the wait', wallSeconds: 0.5 },
]

export interface JobHandle {
  cancel: () => void
}

// Drives progress 0..1 over `wallSeconds` of real time, but always reports the
// remaining time as a fraction of the true ~5-minute job.
export function runJob(
  wallSeconds: number,
  onTick: (progress: number, remainingRealSeconds: number) => void,
  onDone: () => void,
): JobHandle {
  const start = performance.now()
  let frame = 0
  let cancelled = false
  const tick = () => {
    if (cancelled) return
    const elapsed = (performance.now() - start) / 1000
    const p = wallSeconds <= 0 ? 1 : Math.min(1, elapsed / wallSeconds)
    onTick(p, Math.max(0, REAL_JOB_SECONDS * (1 - p)))
    if (p >= 1) {
      onDone()
      return
    }
    frame = requestAnimationFrame(tick)
  }
  frame = requestAnimationFrame(tick)
  return {
    cancel: () => {
      cancelled = true
      cancelAnimationFrame(frame)
    },
  }
}
