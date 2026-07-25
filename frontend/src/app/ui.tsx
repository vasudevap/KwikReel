// Presentational primitives, on the real contract types (contracts.ts).
import React from 'react'
import type { Clip, Origin, Project, ReasonRecord, Segment, SegmentsProposal, SourceIndex } from '../types/contracts'
import { syntheticThumb } from '../thumbs'

type OriginValue = Origin['segments']
type Disposition = SegmentsProposal['disposition']

export function fmtDur(s: number): string {
  if (s < 60) return `${s.toFixed(1)}s`
  return `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`
}
export function baseName(path: string): string {
  return (path.split('/').pop() || path).replace(/\.[^.]+$/, '').replace(/_/g, ' ')
}
export function segDur(segs: Segment[]): number {
  return segs.reduce((a, s) => a + (s.out_s - s.in_s), 0)
}
export function timelineTotal(p: Project): number {
  return p.clips.filter((c) => c.included && !c.deleted).reduce((a, c) => a + segDur(c.segments), 0)
}
export function sourceOf(p: Project, c: Clip): SourceIndex | undefined {
  return p.sources.find((s) => s.source_id === c.source_id)
}
export function orderedClips(p: Project): Clip[] {
  return [...p.clips].sort((a, b) => a.order - b.order)
}

export function ClipThumb({ source, w = 54 }: { source: SourceIndex; w?: number }) {
  const landscape = source.orientation === 'landscape'
  const h = Math.round(landscape ? w * (9 / 16) : w * (16 / 9))
  return <img className="thumb" src={syntheticThumb(source.source_id, baseName(source.path), fmtDur(source.duration_s), landscape)} width={w} height={h} alt="" />
}

export function TrimBar({ durationS, segments, proposal }: { durationS: number; segments: Segment[]; proposal?: Segment[] }) {
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
            <span className="code">{r.code} · {r.confidence}</span>
            <span className="refs">{r.evidence_refs.join(', ')}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

export function OriginBadge({ o }: { o: OriginValue }) {
  return <span className={`badge ${o}`}>origin: {o}</span>
}
export function DispositionBadge({ d }: { d: Disposition }) {
  return <span className={`badge ${d}`}>{d}</span>
}

export function Progress({ label, progress }: { label: string; progress: number }) {
  return (
    <div className="panel">
      <div className="row spread"><strong>{label}</strong><span className="small muted">{Math.round(progress * 100)}%</span></div>
      <div className="progress"><div style={{ width: `${progress * 100}%` }} /></div>
    </div>
  )
}

export interface StepDef { id: string; label: string; gate?: boolean; inert?: boolean }

export function StageBar({ left, right }: { left?: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="stagebar">
      <div className="stagebar-left row wrap">{left}</div>
      <div className="stagebar-right row wrap">{right}</div>
    </div>
  )
}

export function Stepper({ steps, currentIdx, doneIds }: { steps: StepDef[]; currentIdx: number; doneIds: Set<string> }) {
  return (
    <div className="stepper">
      {steps.map((s, i) => (
        <React.Fragment key={s.id}>
          {i > 0 && <span className="step-sep">›</span>}
          <span className={['step', i === currentIdx ? 'current' : '', doneIds.has(s.id) ? 'done' : '', s.inert ? 'inert' : ''].filter(Boolean).join(' ')}>
            {s.label}{s.gate ? <span className="gate"> · gate</span> : null}{s.inert ? ' (later)' : null}
          </span>
        </React.Fragment>
      ))}
    </div>
  )
}
