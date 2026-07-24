# fixtures/synthetic/ — committed, synthetic / rights-cleared only

Per **ADR-013**, only synthetic or rights-cleared assets live here — **no real
footage, no real people.** This directory is the *only* fixtures path tracked by
git (see `.gitignore`).

The WO-100 prototype generates its thumbnails synthetically in code (deterministic
colour blocks per clip), so no image files are required here yet. Any asset added
later must be synthetic/rights-cleared.

Real-footage thumbnails for readability testing go in `../local/` (gitignored,
never committed), behind a self-consent + lifecycle note recorded before
extraction.
