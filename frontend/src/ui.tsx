import React from 'react'
import type { Disposition, Origin, ReasonRecord, Segment, SourceIndex } from './types'
import { syntheticThumb } from './thumbs'
import { DEMO_SPEEDS, type DemoSpeed } from './fakeAsync'

export function fmtDur(s: number): string {
  if (s < 60) return `${s.toFixed(1)}s`
  const m = Math.floor(s / 60)
  const r = Math.round(s % 60)
  return `${m}:${String(r).padStart(2, '0')}`
}
export function fmtRemain(s: number): string {
  const m = Math.floor(s / 60)
  const r = Math.round(s % 60)
  return m > 0 ? `${m}m ${String(r).padStart(2, '0')}s` : `${r}s`
}
export function baseName(path: string): string {
  const b = path.split('/').pop() || path
  return b.replace(/\.[^.]+$/, '').replace(/_/g, ' ')
}

export function ClipThumb({ source, w = 54 }: { source: SourceIndex; w?: number }) {
  const landscape = source.orientation === 'landscape'
  const h = Math.round(landscape ? w * (9 / 16) : w * (16 / 9))
  const src = syntheticThumb(source.source_id, baseName(source.path), fmtDur(source.duration_s), landscape)
  return <img className="thumb" src={src} width={w} height={h} alt="" />
}

// Full-width bar = clip duration; filled = kept (effective); dashed = the AI proposal.
export function TrimBar({
  durationS,
  segments,
  proposal,
}: {
  durationS: number
  segments: Segment[]
  proposal?: Segment[]
}) {
  const pct = (x: number) => `${durationS > 0 ? (x / durationS) * 100 : 0}%`
  return (
    <div className="trimbar" title={`${durationS.toFixed(1)}s clip`}>
      <div className="cut" style={{ left: 0, right: 0 }} />
      {segments.map((s, i) => (
        <div key={i} className="kept" style={{ left: pct(s.in_s), width: pct(s.out_s - s.in_s) }} />
      ))}
      {proposal?.map((s, i) => (
        <div key={'p' + i} className="prop" style={{ left: pct(s.in_s), width: pct(s.out_s - s.in_s) }} />
      ))}
    </div>
  )
}

export function ReasonList({ reasons }: { reasons: ReasonRecord[] }) {
  return (
    <div>
      {reasons.map((r, i) => (
        <div className="reason" key={i}>
          <div>{r.human_text}</div>
          <div className="row spread">
            <span className="code">
              {r.code} · {r.confidence}
            </span>
            <span className="refs">{r.evidence_refs.join(', ')}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

export function OriginBadge({ o }: { o: Origin }) {
  return <span className={`badge ${o}`}>origin: {o}</span>
}
export function DispositionBadge({ d }: { d: Disposition }) {
  return <span className={`badge ${d}`}>{d}</span>
}

export function JobProgress({
  label,
  progress,
  remainingRealS,
  speed,
  onSpeed,
}: {
  label: string
  progress: number
  remainingRealS: number
  speed: DemoSpeed
  onSpeed: (s: DemoSpeed) => void
}) {
  return (
    <div className="panel">
      <div className="row spread">
        <strong>{label}</strong>
        <span className="small muted">{Math.round(progress * 100)}%</span>
      </div>
      <div className="progress">
        <div style={{ width: `${progress * 100}%` }} />
      </div>
      <p className="small muted" style={{ margin: '8px 0 0' }}>
        About <strong>{fmtRemain(remainingRealS)}</strong> left at production speed (this is a ~5-minute job).
        You can leave this screen — the work keeps running.
      </p>
      <div className="row small wrap" style={{ marginTop: 6 }}>
        <span className="muted">Demo speed:</span>
        {DEMO_SPEEDS.map((s) => (
          <button key={s.id} className={speed === s.id ? 'primary' : ''} onClick={() => onSpeed(s.id)}>
            {s.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export interface StepDef {
  id: string
  label: string
  gate?: boolean
  inert?: boolean
}

// Consistent top action bar for every stage: forward/advance actions go on the
// right, in-page actions (e.g. "AI Trim all") and back-nav go on the left.
export function StageBar({ left, right }: { left?: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="stagebar">
      <div className="stagebar-left row wrap">{left}</div>
      <div className="stagebar-right row wrap">{right}</div>
    </div>
  )
}
export function Stepper({
  steps,
  currentIdx,
  doneIds,
}: {
  steps: StepDef[]
  currentIdx: number
  doneIds: Set<string>
}) {
  return (
    <div className="stepper">
      {steps.map((s, i) => (
        <React.Fragment key={s.id}>
          {i > 0 && <span className="step-sep">›</span>}
          <span
            className={[
              'step',
              i === currentIdx ? 'current' : '',
              doneIds.has(s.id) ? 'done' : '',
              s.inert ? 'inert' : '',
            ]
              .filter(Boolean)
              .join(' ')}
          >
            {s.label}
            {s.gate ? <span className="gate"> · gate</span> : null}
            {s.inert ? ' (later)' : null}
          </span>
        </React.Fragment>
      ))}
    </div>
  )
}
