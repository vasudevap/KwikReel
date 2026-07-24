// In-memory project store — the prototype's stand-in for WO-103. Every mutation
// enforces the ES-001 §4.1 invariants so the flow behaves like the real thing:
//   - every field mutation writes `origin` ("user" on a human edit)
//   - a proposal never overwrites a "user" field except an explicit re-run
//   - `deleted` is a flag; the clip object is retained for exact restore
//   - `order` stays dense and unique across non-deleted clips
//   - every proposal carries a `disposition`
//   - editing after a finalize approval resets that approval (§7)
import type {
  Clip,
  Project,
  Segment,
  SegmentsProposal,
  SourceIndex,
  StageApprovals,
} from './types'

const now = () => new Date().toISOString()

function mapClip(p: Project, id: string, fn: (c: Clip) => Clip): Project {
  return { ...p, updated_at: now(), clips: p.clips.map((c) => (c.source_id === id ? fn(c) : c)) }
}

// Any content edit invalidates a prior finalize approval (§7 / WO-109 gate).
function bustFinalize(p: Project): Project {
  if (!p.stage_approvals.finalize) return p
  return { ...p, stage_approvals: { ...p.stage_approvals, finalize: null } }
}

// ---- selectors ---------------------------------------------------------------

export function fullClip(s: SourceIndex): Segment {
  return { in_s: 0, out_s: s.duration_s, speed: [] }
}
export function clipRenderSeconds(c: Clip): number {
  return c.segments.reduce((sum, seg) => sum + Math.max(0, seg.out_s - seg.in_s), 0)
}
export function liveClips(p: Project): Clip[] {
  return p.clips.filter((c) => !c.deleted).sort((a, b) => a.order - b.order)
}
export function renderClips(p: Project): Clip[] {
  return liveClips(p).filter((c) => c.included)
}
export function timelineSeconds(p: Project): number {
  return renderClips(p).reduce((sum, c) => sum + clipRenderSeconds(c), 0)
}
export function sourceOf(p: Project, id: string): SourceIndex {
  const s = p.sources.find((x) => x.source_id === id)
  if (!s) throw new Error(`no source ${id}`)
  return s
}

// ---- curation (§5.5, ADR-009) ------------------------------------------------

export function setIncluded(p: Project, id: string, included: boolean): Project {
  return bustFinalize(
    mapClip(p, id, (c) => ({ ...c, included, origin: { ...c.origin, included: 'user' } })),
  )
}
export function setDeleted(p: Project, id: string, deleted: boolean): Project {
  // deletion is a flag; the clip object is retained so restore is exact.
  return bustFinalize(
    mapClip(p, id, (c) => ({ ...c, deleted, origin: { ...c.origin, included: 'user' } })),
  )
}
export function move(p: Project, id: string, dir: -1 | 1): Project {
  const live = liveClips(p)
  const i = live.findIndex((c) => c.source_id === id)
  const j = i + dir
  if (i < 0 || j < 0 || j >= live.length) return p
  const a = live[i]
  const b = live[j]
  // swap order values -> stays dense and unique
  let next = mapClip(p, a.source_id, (c) => ({
    ...c,
    order: b.order,
    origin: { ...c.origin, order: 'user' },
  }))
  next = mapClip(next, b.source_id, (c) => ({
    ...c,
    order: a.order,
    origin: { ...c.origin, order: 'user' },
  }))
  return bustFinalize(next)
}

// ---- trim assist controls (§5.3, ADR-007/010) --------------------------------

// User runs the assist on a clip: copy the latent proposal in, disposition
// "pending", effective segments become the proposed value (origin "proposed").
export function applyProposal(p: Project, id: string, proposal: SegmentsProposal): Project {
  return bustFinalize(
    mapClip(p, id, (c) => ({
      ...c,
      segments: proposal.value,
      origin: { ...c.origin, segments: 'proposed' },
      proposals: { ...c.proposals, segments: { ...proposal, disposition: 'pending' } },
    })),
  )
}
// Adjust: user drags handles. origin "user", disposition "adjusted", proposal retained.
export function adjustTrim(p: Project, id: string, segments: Segment[]): Project {
  return bustFinalize(
    mapClip(p, id, (c) => ({
      ...c,
      segments,
      origin: { ...c.origin, segments: 'user' },
      proposals: {
        ...c.proposals,
        segments: c.proposals.segments
          ? { ...c.proposals.segments, disposition: 'adjusted' }
          : c.proposals.segments,
      },
    })),
  )
}
// Remove suggestion: revert to full clip. origin "user", disposition "dismissed", proposal retained.
export function removeTrim(p: Project, id: string): Project {
  return bustFinalize(
    mapClip(p, id, (c) => ({
      ...c,
      segments: [fullClip(sourceOf(p, id))],
      origin: { ...c.origin, segments: 'user' },
      proposals: {
        ...c.proposals,
        segments: c.proposals.segments
          ? { ...c.proposals.segments, disposition: 'dismissed' }
          : c.proposals.segments,
      },
    })),
  )
}
// Re-run: the ONLY path that overwrites a "user" value. Fresh proposal, "pending".
export function rerunTrim(p: Project, id: string, proposal: SegmentsProposal): Project {
  return applyProposal(p, id, { ...proposal, at: now() })
}

// ---- stage approval (§7) -----------------------------------------------------

export function approveStage(p: Project, stage: keyof StageApprovals): Project {
  const stamp = now()
  let clips = p.clips
  if (stage === 'trim') {
    // approving trim promotes every untouched (pending) proposal to accepted.
    clips = p.clips.map((c) =>
      c.proposals.segments && c.proposals.segments.disposition === 'pending'
        ? {
            ...c,
            proposals: {
              ...c.proposals,
              segments: { ...c.proposals.segments, disposition: 'accepted' },
            },
          }
        : c,
    )
  }
  return { ...p, updated_at: stamp, clips, stage_approvals: { ...p.stage_approvals, [stage]: stamp } }
}
export function unapproveStage(p: Project, stage: keyof StageApprovals): Project {
  return { ...p, updated_at: now(), stage_approvals: { ...p.stage_approvals, [stage]: null } }
}
