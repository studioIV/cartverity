# Changelog

## 0.2.0-alpha.5

- Give completed scans a brighter result panel with the outcome, reference and
  final stats in place of completed progress bars.
- Separate physical-button controls from content with high-contrast labeled
  badges in a footer; no touch input or key actions are added.
- Refresh summary, hash, SD report and reference-source pages. Scan coverage,
  reference decisions and session settings are unchanged.
- Keep cancellation at the final read from displaying an agreement claim before
  the final comparison; display SD report failures separately from the ROM verdict.

## 0.2.0-alpha.4

- Reference tools correction: accept official No-Intro exports that list individual
  contributors in author and identify the project in homepage/URL. Preserve
  contributor attribution in the importer report. Firmware is unchanged.

- Add offline No-Intro XML DAT import and exact whole-ROM SHA-1/size lookup.
- Validate bounded databases with metadata, order, size and CRC checks; keep
  missing entries unverified and per-game sidecars first priority.
- Display/log original DAT name, version, SHA-256, official URL and matched title.
- Package PC reference tools and source attribution. No real catalog is bundled.
- Consolidate the repository around the standalone app; remove obsolete script,
  script-only checks, duplicated legacy docs and the outdated preview.
- Keep firmware, reference tools, quick start, matching source and checksums as
  the release assets. Preserve older GPL sources separately when consolidating releases.

## Earlier standalone work

- Alpha.3 added by studioIV branding.
- Alpha.2 introduced RAM/changed-pixel presentation and Y-button session settings.
- Alpha.1 introduced the dedicated two-pass checker, metrics, region comparison,
  checked SD logs and the initializer save-probe bypass.

The retired v0.1.0 script remains in Git history. Hardware validation is distinct
from automated build and host-test results; see [testing](docs/TESTING.md).
