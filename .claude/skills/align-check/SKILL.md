---
name: align-check
description: Drift check for KwikReel — verify the briefing docs, the ADP record, the evidence ledger, and the test suite still agree with git reality. Run at session start before building, after any batch of doc edits, and at ADP closeout. Non-Claude agents can follow it as a plain checklist.
---

# Align-check — the drift check

The playbook's Stage D names "periodic drift checks"; this is that check, made
concrete for KwikReel. It exists because drift really happened: on 2026-07-29
an audit found 24 commits of build behind briefing docs that still described
the pre-build world. Every step below is a plain command or a read, so
non-Claude agents can run it as an ordered checklist.

**Finding drift is the check working, not a problem to argue around. Fix the
record, not the history.**

## 1 · Ground truth first

```bash
git log --format='%h %ad %s' --date=format:'%Y-%m-%d %H:%M' -15
git status -sb
git log -1 --format='%h %ad %s' -- CLAUDE.md
git log -1 --format='%h %ad %s' -- handoff.md
```

If `handoff.md` has moved well past `CLAUDE.md` and state-changing commits sit
between them, suspect briefing drift and read on with that in mind.

## 2 · The briefing layer against reality

- **CLAUDE.md / AGENTS.md, "Where the project is":** does every sentence match
  §1's git evidence? The two files must also mirror each other — if they
  diverge, `CLAUDE.md` is authoritative and `AGENTS.md` is stale; say so
  rather than silently picking one.
- **handoff.md:** header date, the suite box, "In flight", the stop-and-ask
  ledger, and the owner-actions list — each against what §1 and §3 show.
- **README.md status section:** no claim the current suite or authorization
  state contradicts.

## 3 · The suite, actually run

```bash
.venv/bin/python -m pytest --continue-on-collection-errors --tb=no -q
```

A bare `pytest` halts at expected import errors mid-rebuild — always pass the
flag. Compare pass/fail/error counts *and the failing module names* against
handoff.md's warning box. Worse than the box is a regression; better means the
box is stale. Either way something changes this session.

## 4 · The authorization record is self-consistent

- The live ADP agrees with itself: the head's amendment notes, the §8
  authorization block, and the §9 closeout condition carry the same amendment
  count, the same WO scope, the same gates.
- Every amendment at the head also appears in `handoff.md`.
- The withholds are still mirrored onto the tool: `git push` and `gh` remain
  on the ask list in `.claude/settings.local.json` (Claude sessions), per the
  playbook's enforcement-manifest rule.

## 5 · Stale-phrase sweep

```bash
grep -rn --include='*.md' -E 'four things it does not yet settle|drafted and unsigned|Tests are green|waits on .*SO-1|are \*\*undecided\*\*|Drafted, unsigned|amended same day twice' . | grep -v docs/archive | grep -v .claude/skills
```

A hit outside `docs/archive/` is a finding unless the document is quoting the
wording it corrected (amendment notes do this legitimately). **Maintain this
pattern list**: when new drift is found and fixed, add its telltale phrase
here in the same commit.

## 6 · Guardrail spot-checks (cheap, always)

```bash
git ls-files | grep -iE '\.(mov|mp4|m4v|avi|jpg|jpeg|png|heic|wav|aac|m4a|mp3)$'
git ls-files docs/design-claude docs/archive/design-claude
git status -sb | head -1
```

The first two must be empty. Ahead of `origin` is expected — pushes are
per-action owner decisions. **Behind `origin` means someone pushed: stop and
tell the owner before doing anything else.**

## 7 · Report and repair

State what was checked, what disagreed, and why. Fix record-layer drift as one
commit (see `CLAUDE.md` → *How work is recorded* for which documents move
together); a genuine code regression is not record drift and is handled as
code. If a fix needs an owner decision — an ADP amendment, a `DECISIONS.md`
entry — present the finding and stop; the written entry is how a decision
lands, not the conversation.
