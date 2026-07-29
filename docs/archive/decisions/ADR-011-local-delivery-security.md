# ADR-011 — Local delivery security posture

**Status:** Accepted — owner-approved 2026-07-24 (pre-ADP course correction).
**Operationalizes:** [ADR-002](ADR-002-privacy-and-data-posture.md) (no egress of media, derivatives, or paths) and [ADR-005](ADR-005-editor-form-factor.md) (local web app on localhost) for the **served application**. Adds the application-security layer that "bind to `127.0.0.1`" does not by itself provide. Relaxes neither.
**Relates to:** [ES-001](../specs/ES-001-manual-editor-core.md) §9, WO-106, WO-113.
**Authorizes nothing.**

## Context

ADR-005 binds the backend to `127.0.0.1` and forbids outbound network. The review noted this stops *remote* hosts but not *other local origins*: **any web page open in the user's browser can issue requests to `http://127.0.0.1:PORT`** (localhost CSRF / DNS-rebinding class). Unprotected, a malicious page could `POST /api/export` or `/api/render`, or probe `/api/project/{id}` to read the absolute media paths — which by ADR-002's own threat model reveal where a family lives. "Bound to localhost" is a partial control for a product branded on private-footage safety.

## Decision — locked, relaxable only by a new ADR

- **Host / Origin allow-listing.** Reject requests whose `Origin`/`Referer` is cross-site; validate the `Host` header against an allow-list (blunts DNS-rebinding).
- **No permissive CORS.** No `Access-Control-Allow-Origin: *`, no wildcard credentials. Default-deny; the local frontend is same-origin.
- **Capability-style local session token.** A random token minted per launch, delivered to the local UI same-origin (launch URL / same-origin config) and **required on state-changing endpoints**, so a blind cross-site `POST` cannot act without reading a same-origin-only secret.
- **Path scrubbing.** The `{error_code, human_text, remediation}` envelope, job errors, logs, and any surfaced field must **not** leak absolute media paths — reduced to basenames or redacted in anything user- or log-facing.
- **Tests are guards (WO-113).** Each protection **fails when removed**: a cross-origin `POST` is rejected; a missing/invalid token is rejected; a wildcard-CORS config fails the build; an error carrying an absolute path fails.
- **Binding beyond `127.0.0.1` remains a stop-and-ask** (unchanged from ADR-005; the deferred phone-access path trips it).

## Relationship to WO-100 (does this block the prototype?)

**No.** WO-100 is a fake-data React prototype with **no backend** (it excludes any real processing). The local API does not exist in WO-100, so this posture does not block it. It is required in **ES-001 §9 before WO-101 freezes the contract**, and implemented by **WO-106** (the API) with guards in **WO-113**.

## Consequences

- The local-first privacy claim is enforced against the realistic *local* attacker, not only remote ones.
- Small, standard middleware cost; no product code is written by this record (spec + guards only).
- The security posture is now a hard constraint an implementing agent may not relax under its own judgment.
