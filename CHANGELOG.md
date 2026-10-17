# Changelog

## 0.2.0-alpha.1 - 2026-10-18 (native experimental)

- Add a dedicated GodMode9-based 3DS `.firm` dashboard with live overall/pass
  bars, throughput, elapsed time, ETA and changed logical-region counts.
- Reinitialize cartridge access before each pass; compare whole-ROM SHA-1 and
  1 MiB CRC32 regions. Preserve read-only operation and optional references.
- Add checked unique SD reports, cancellation, rescan and result/detail pages.
- Build ARM firmware in CI with complete GPL corresponding source, environment
  information and checksums. Add compiled C core and UI tests plus a host preview.
- Keep the original `.gm9` release available. Native hardware validation pending.

## 0.1.0 - 2026-10-18

Initial GitHub-ready implementation, awaiting hardware testing.

- Full standard NDS view selected from cartridge-info filename.
- Two SHA-1 calculations with separate consistency and reference results.
- Optional binary references created by a strict desktop helper.
- Unique SD logs with incomplete/completed state and failure outcomes.
- Offline static/scenario checks, pinned source checks, and GitHub Actions.
- Documented cache, read-error, reference, and storage limitations.
