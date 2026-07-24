// Synthetic thumbnails only (ADR-013): deterministic colour blocks derived from
// the source id. No real footage, no real people, no remote assets, no image
// files on disk. Real-footage thumbnails for readability testing are a later,
// owner-driven step into fixtures/local/ (gitignored), behind self-consent.

function hashInt(s: string): number {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return Math.abs(h)
}

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// Portrait 9:16 by default (phone footage); landscape swaps the aspect.
export function syntheticThumb(
  seed: string,
  label: string,
  subtitle: string,
  landscape = false,
): string {
  const w = landscape ? 320 : 180
  const h = landscape ? 180 : 320
  const n = hashInt(seed)
  const hue = n % 360
  const hue2 = (hue + 35) % 360
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">` +
    `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">` +
    `<stop offset="0" stop-color="hsl(${hue},52%,46%)"/>` +
    `<stop offset="1" stop-color="hsl(${hue2},52%,28%)"/></linearGradient></defs>` +
    `<rect width="${w}" height="${h}" fill="url(#g)"/>` +
    `<text x="12" y="30" font-family="monospace" font-size="15" fill="rgba(255,255,255,0.96)">${esc(label)}</text>` +
    `<text x="12" y="50" font-family="monospace" font-size="11" fill="rgba(255,255,255,0.78)">${esc(subtitle)}</text>` +
    `<text x="12" y="${h - 12}" font-family="monospace" font-size="9" fill="rgba(255,255,255,0.6)">synthetic · not real footage</text>` +
    `</svg>`
  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg)
}
