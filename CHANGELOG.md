# Changelog

## 0.2.0-alpha.4 - 2026-10-18

- Import user-downloaded No-Intro Nintendo DS XML DATs into a bounded offline
  database with source name/version, original DAT SHA-256 and official URL.
- Validate database bounds, strings, ordering, reserved bytes and CRC32; require
  exact whole-ROM SHA-1 and size after two consistent reads for MATCHES_DATABASE.
- Keep missing database entries unverified, and per-game sidecars first priority.
  Add reference-source details and provenance fields in scan logs.
- Package reference tools and document No-Intro attribution, format compatibility,
  source boundaries and setup. No real DAT, reference catalog or ROMs are bundled.
- Add importer, cross-language lookup/corruption and source-page tests.

## Documentation refresh — 2026-10-18

- Make standalone alpha.3 the main README/install/download path.
- Add tutorials for installation, controls/settings, references, updates and
  troubleshooting; document native logs and current limitations.
- Separate legacy script instructions/logs/limits and update hardware reports,
  validation and GPL source-distribution notes. No firmware behavior changed.

## 0.2.0-alpha.3 - 2026-10-18

- Display `by studioIV` on the top screen across all pages and in the README.
- Preserve existing copyright, licensing and upstream GodMode9 notices.

## 0.2.0-alpha.2 - 2026-10-18

- Render complete dashboard frames in RAM; publish only changed pixels to avoid
  clearing visible screens repeatedly. Default refresh is now 250 ms.
- Add Y-button session settings: refresh rate, brightness, Auto/Require/Ignore
  reference policy and initial result page. X restores defaults.
- Record refresh rate and reference policy in SD logs. Keep two full scan passes
  and the native initializer's save-probe bypass.
- Test unchanged-pixel preservation, settings wrap/bounds and settings-screen
  drawing. Physical flicker and controls testing remains required.

## 0.2.0-alpha.1 - 2026-10-18 (native experimental)

- Add a dedicated GodMode9-based 3DS `.firm` dashboard with live overall/pass
  bars, throughput, elapsed time, ETA and changed logical-region counts.
- Reinitialize cartridge access before each pass; compare whole-ROM SHA-1 and
  1 MiB CRC32 regions. Preserve read-only operation and optional references.
- Bypass upstream save-chip detection in native builds: stock GodMode9's EEPROM
  capacity probe can write/restore a save byte. Document that script limitation
  and audit the native initializer's active preprocessed code in CI.
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
