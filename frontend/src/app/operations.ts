import { cloneProject } from './state.ts'
import type {
  ClipPatchInput,
  ProjectPatchInput,
  ProjectWriteOperation,
} from './types.ts'
import type { Project } from '../types/contracts.ts'

function requireClip(project: Project, sourceId: string) {
  const clip = project.clips.find((item) => item.source_id === sourceId)
  if (!clip) throw new Error(`unknown source ${sourceId}`)
  return clip
}

export function projectPatchOperation(
  patch: ProjectPatchInput,
): ProjectWriteOperation {
  return {
    label: 'project patch',
    optimistic(project) {
      const next = cloneProject(project)
      Object.assign(next, patch)
      return next
    },
    commit(client, project) {
      return client.patchProject(project.project_id, project.updated_at, patch)
    },
  }
}

export function clipPatchOperation(
  sourceId: string,
  patch: ClipPatchInput,
): ProjectWriteOperation {
  return {
    label: 'clip patch',
    optimistic(project) {
      const next = cloneProject(project)
      const clip = requireClip(next, sourceId)
      Object.assign(clip, patch)
      if (patch.segment !== undefined) clip.origin.segments = 'user'
      if (patch.speed_ranges !== undefined) clip.origin.speed = 'user'
      if (patch.audio !== undefined) clip.origin.audio = 'user'
      return next
    },
    commit(client, project) {
      return client.patchClip(project.project_id, sourceId, project.updated_at, patch)
    },
  }
}

export function binClipOperation(sourceId: string): ProjectWriteOperation {
  return {
    label: 'bin clip',
    optimistic(project) {
      const next = cloneProject(project)
      const clip = requireClip(next, sourceId)
      if (clip.stashed_segment) {
        clip.segment = clip.stashed_segment
        clip.stashed_segment = null
      } else {
        const source = next.sources.find((item) => item.source_id === sourceId)
        clip.stashed_segment =
          clip.segment ?? { in_s: 0, out_s: source?.duration_s ?? 0 }
        clip.segment = { in_s: 0, out_s: 0 }
      }
      clip.origin.segments = 'user'
      return next
    },
    commit(client, project) {
      return client.binClip(project.project_id, sourceId, project.updated_at)
    },
  }
}

export function rejectTrimOperation(sourceId: string): ProjectWriteOperation {
  return {
    label: 'reject trim',
    optimistic(project) {
      const next = cloneProject(project)
      const proposal = requireClip(next, sourceId).proposals.segments
      if (proposal) proposal.disposition = 'dismissed'
      return next
    },
    commit(client, project) {
      return client.rejectTrim(project.project_id, sourceId, project.updated_at)
    },
  }
}

export function relinkClipOperation(
  sourceId: string,
  replacementPath: string,
): ProjectWriteOperation {
  return {
    label: 'relink clip',
    optimistic(project) {
      const next = cloneProject(project)
      const source = next.sources.find((item) => item.source_id === sourceId)
      if (source) source.path = replacementPath
      return next
    },
    commit(client, project) {
      return client.relinkClip(
        project.project_id,
        sourceId,
        project.updated_at,
        replacementPath,
      )
    },
  }
}

export function repairLinksOperation(): ProjectWriteOperation {
  return {
    label: 'repair links',
    optimistic: cloneProject,
    commit(client, project) {
      return client.repairLinks(project.project_id, project.updated_at)
    },
  }
}
