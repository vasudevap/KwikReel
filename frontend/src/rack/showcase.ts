import { createElement as h } from 'react'
import { createRoot } from 'react-dom/client'

import {
  Glass,
  GLYPHS,
  LabeledHousing,
  NameGlass,
  PhysicalKey,
  RackColumns,
  RackFrame,
  RackModule,
  SevenSegment,
} from './primitives.ts'
import './rack.css'

const monitor = h(
  RackModule,
  { className: 'kr-showcase__monitor', label: 'Monitor' },
  h('div', { className: 'kr-showcase__screen' }),
)

const reel = h(
  RackModule,
  { label: 'Reel control' },
  h(
    'div',
    { className: 'kr-showcase__row kr-showcase__spread' },
    h(NameGlass, {
      label: 'Current reel',
      surface: 'reel',
      value: 'Sunday at Hanlan’s Point — family cut',
    }),
    h(SevenSegment, { kind: 'time', label: 'Playhead', value: '02:14' }),
  ),
  h(
    'div',
    { className: 'kr-showcase__row' },
    h(PhysicalKey, { glyph: 'previous', label: 'Previous' }),
    h(PhysicalKey, { glyph: 'play', label: 'Play', ring: 'active' }),
    h(PhysicalKey, { glyph: 'pause', label: 'Pause' }),
    h(PhysicalKey, { glyph: 'next', label: 'Next' }),
    h(PhysicalKey, { label: 'Keep', lamp: 'active' }),
    h(PhysicalKey, { label: 'Review', lamp: 'attention' }),
  ),
)

const glass = h(
  RackModule,
  { label: 'Proposal glass' },
  h(
    Glass,
    { className: 'kr-showcase__glass', label: 'Proposal', variant: 'vfd' },
    h('strong', null, 'PROPOSED · TRIM'),
    h('span', null, 'Hold the laugh; leave 08 frames before the cut.'),
  ),
  h(
    'div',
    { className: 'kr-showcase__row' },
    h(PhysicalKey, { glyph: 'reject', label: 'Reject' }),
    h(PhysicalKey, { glyph: 'rerun', label: 'Rerun', ring: 'attention' }),
    h(PhysicalKey, { glyph: 'pencil', label: 'Edit' }),
    h('span', { className: 'kr-grow' }),
    h(SevenSegment, { kind: 'rate', label: 'Playback rate', small: true, value: '1.0×' }),
  ),
)

const housing = h(
  RackModule,
  { label: 'Locked housing' },
  h(
    'div',
    { className: 'kr-showcase__row kr-showcase__spread' },
    h(
      LabeledHousing,
      { label: 'Index window · fixed 232', locked: true },
      h(
        'div',
        { className: 'kr-showcase__housing-body' },
        h('span', null, '01–04 / 12'),
        h(SevenSegment, {
          kind: 'windowRange',
          label: 'Visible index window',
          small: true,
          value: '0001–0004',
        }),
      ),
    ),
    h(SevenSegment, { kind: 'queue', label: 'Queue', value: '000000012' }),
  ),
)

const glyphs = h(
  RackModule,
  { label: 'Physical key glyphs' },
  h(
    'div',
    { className: 'kr-showcase__glyph-grid' },
    ...GLYPHS.map((glyph) => h(PhysicalKey, { glyph, key: glyph, label: glyph })),
  ),
)

const instruments = h('div', null, reel, glass, housing, glyphs)

createRoot(document.getElementById('root') as HTMLElement).render(
  h(RackFrame, null, h(RackColumns, { instruments, monitor })),
)
