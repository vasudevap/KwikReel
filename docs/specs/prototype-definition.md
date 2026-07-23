# Prototype definition and architecture assessment

**Status:** Draft; implementation is not authorized.

## Smallest technically credible POC

Run locally against 20–50 clips and one local, royalty-free test track. Generate `analysis.json`, `timeline.json`, a human-readable report, and `draft.mp4`.

0. Accept 3–10 user-marked **must-include** clips before analysis. Marked clips are never rejected, and their inclusion is recorded as user-declared rather than inferred. This is cheap insurance against ranking failure and belongs in the first working version, not a later phase.
1. Inventory clips using FFprobe; retain timestamps/orientation/duration and generate low-resolution proxies.
2. Sample frames and calculate blur, brightness/exposure proxy, motion/shake proxy, duration, and visual embeddings/hashes.
3. Detect **audio events** — laughter, cheering, splashes, exclamations — across the clip's audio track. This is a cheap importance signal that is often stronger than visual cues for identifying a family moment, and the earlier draft of this document omitted it entirely.
4. Flag corrupt, empty, poor-quality, and near-duplicate clips—but retain all sources and reasons.
5. Cluster clips by capture time plus visual similarity; choose 1–3 candidate subclips per usable clip using motion energy peaks, audio-event peaks, and face saliency to propose windows.
6. Score candidates with deterministic signals: technical quality, uniqueness, scene motion, audio-event salience, event coverage, and user-declared importance (highest weight when present).
7. Detect track beats and sections; use a constrained chronological optimizer to choose candidates under the duration budget.
8. Snap eligible cuts to a **subset** of strong beats, align section boundaries with event transitions, vertical crop/pad, and render through FFmpeg. **Speed changes are advisory flags only — never applied automatically.** A wrong speed ramp reads as kitsch instantly, and the failure is viscerally obvious to users.
9. Emit selection, rejection, and timing rationale per source in plain language a user can read.

### Explicit POC exclusions

No facial identification, automatic publishing, cloud upload, commercial-track extraction, generative video, custom model training, heavy transitions, or polished editor.

## Architecture options

| Dimension | Local-first | Cloud-first | Hybrid |
|---|---|---|---|
| Processing | Mac invokes local media/ML tools; source stays on device. | Upload originals/proxies to managed workers and APIs. | Local proxy/quality/render; opt-in cloud multimodal scoring on reduced/redacted media. |
| Strengths | Privacy, no upload wait/cost, offline, simpler retention. | Elastic compute; frontier model access; simpler cross-device collaboration. | Improves semantic quality while bounding data transfer and preserving local export. |
| Risks | Hardware variance, model distribution/licensing, slower on weak machines. | Family-media privacy, retention/security, egress/inference costs, upload latency. | Two trust boundaries and complex consent/failure behavior. |
| Best use | **POC recommendation.** | Only if benchmark proves local semantics inadequate and consent/cost controls are viable. | Candidate after POC; cloud scorer must be optional and replaceable. |

## Component boundaries

```text
Folder → Inventory/Proxies → Analysis → Candidate builder → Timeline planner → Renderer
                    ↓              ↓              ↓                 ↓
               source index    analysis.json  timeline.json      draft.mp4
```

- `analysis.json`: immutable clip facts/signals, model/tool versions, and rejection reasons.
- `timeline.json`: selected source ranges, crop/speed/audio/transition decisions, rationale, and beat references.
- Renderer is deterministic from `timeline.json`; it cannot delete sources or publish outputs.

## Practical technology assessment

- **FFmpeg/FFprobe:** required baseline for reliable metadata, proxy generation, filters, H.264/AAC render.
- **OpenCV:** viable for frame sampling, blur and brightness signals; treat shake as a proxy, not an automatic discard verdict.
- **Perceptual hash/embeddings:** use hashes for simple near-duplicates; benchmark a local CLIP-family embedding only if it materially improves duplicate/event grouping.
- **PySceneDetect:** optional candidate-boundary proposal; phone clips often contain one continuous shot, so quality/motion windows remain necessary.
- **Beat detector:** benchmark librosa against hand-marked beats; protect sections from mechanical every-beat cuts. **`madmom` and Essentia are excluded** despite their accuracy — GPL and AGPLv3 copyleft (respectively) make them distribution-restricting and unsafe for a potentially distributed product (ADR-003). An earlier draft of this document proposed benchmarking it; that was an error.
- **Audio event detection:** YAMNet or PANNs for laughter, cheering, and splash detection. Cheap, on-device, and frequently a better "family moment" signal than any visual cue. Whisper is **not** needed — vacation footage is rarely speech-driven, and transcription adds cost, latency, and privacy exposure for no measured benefit.
- **Apple Vision framework:** free, on-device, well maintained. Provides face detection and landmarks, saliency, and built-in aesthetics/quality scoring. Preferred over rolling equivalent signals by hand. **Detection and counting only — no identity recognition** (ADR-002). MediaPipe is the cross-platform fallback if portability ever matters.
- **Multimodal model:** experiment later as a scorer/adviser, not an authority. It must return structured labels/rationales and never bypass the timeline constraints.
- **Apple Silicon:** exploit VideoToolbox through FFmpeg where available; hardware and codec compatibility need measured verification on the target Mac.

## Output and handoff

The POC exports 1080×1920 H.264/AAC MP4 and canonical JSON. Add FCPXML/Premiere interchange only after core quality passes; CapCut has no documented direct third-party project import/export support in its help center, so MP4 is the reliable early handoff.
