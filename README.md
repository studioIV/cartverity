# CartVerity

by **studioIV**

[![Firmware](https://github.com/studioIV/cartverity/actions/workflows/native.yml/badge.svg)](https://github.com/studioIV/cartverity/actions/workflows/native.yml)
[![Reference tools](https://github.com/studioIV/cartverity/actions/workflows/check.yml/badge.svg)](https://github.com/studioIV/cartverity/actions/workflows/check.yml)

A standalone Nintendo DS cartridge integrity checker for Nintendo 3DS, developed
for New Nintendo 3DS XL. Boot directly into a dual-screen dashboard to compare
two complete ROM reads and, optionally, a supplied reference or offline database.

**[Download alpha.5](https://github.com/studioIV/cartverity/releases/tag/v0.2.0-alpha.5)**
· [Firmware only](https://github.com/studioIV/cartverity/releases/download/v0.2.0-alpha.5/CartVerity-v0.2.0-alpha.5.firm)
· [Reference tools](https://github.com/studioIV/cartverity/releases/download/v0.2.0-alpha.5/CartVerity-reference-tools.zip)

Experimental: automated tests and builds do not certify hardware behavior.
Consistent reads without a trustworthy reference remain **unverified**.

## Quick start

1. On an already configured Luma3DS console, copy `CartVerity-v0.2.0-alpha.5.firm` to
   `SD:/luma/payloads/`. Keep your working GodMode9 payload.
2. Power off, insert an original standard DS cartridge, then hold **START**
   while powering on and select **CartVerity**.
3. Press **A** to scan. Leave the cartridge and SD inserted during both passes.
4. Press **X** at the result for hashes, SD report and reference-source details.
   Press **Y** outside a scan for settings.

Do not replace `boot.firm` or flash this payload to NAND. No script or Lua file
is needed. [Full installation and update instructions](docs/INSTALL.md).

## Features

- Two full normalized-ROM SHA-1 passes, with cartridge initialization before
  each pass and CRC32 comparison of 1 MiB logical regions.
- Overall/pass bars, average speed, elapsed time, ETA and differing-region counts.
- A bright result panel prioritizes the outcome, reference and final scan stats.
- Physical-button controls appear as labeled badges in a separate footer.
- RAM rendering with changed-pixel updates to reduce visible redraw flicker.
- Session settings for refresh, brightness, reference policy and initial result page.
- Per-game SHA-1 sidecars or an imported No-Intro database; unique SD reports.

The app bypasses GodMode9's save-capacity probe and writes only SD report files.
It does not modify cartridge ROM, saves or NAND, save ROM dumps, or repair carts.
Standard DS carts up to 512 MiB are accepted; 3DS and DSi-enhanced carts are
rejected. Special-storage/flashcart compatibility is not claimed.

## Reference data

Catalog metadata and hashes come from **[No-Intro](https://no-intro.org/)**,
distributed through **[DAT-o-MATIC](https://datomatic.no-intro.org/)**.
Download a compatible full decrypted/normalized Nintendo DS XML DAT and import
it with `tools/import_dat.py`. Put the output at:

```text
SD:/gm9/support/cartverity/nds.cvdb
```

The console checks exact whole-ROM SHA-1 **and size** after two consistent reads.
A match reports `MATCHES_DATABASE`; a missing entry remains unverified. Per-game
`.nds.sha1` sidecars take priority. No real DAT/database or ROMs are bundled.

The original DAT name, version, SHA-256 and official source URL appear in the
reference-source page and logs. This records provenance, not authentication.
CartVerity is not affiliated with No-Intro. [Source attribution](docs/REFERENCE_SOURCES.md)
· [No-Intro DS DAT notes](https://wiki.no-intro.org/index.php?title=Nintendo_-_Nintendo_DS_dat_notes).

## Guides

| Guide | Covers |
| --- | --- |
| [Install and update](docs/INSTALL.md) | SD layout, booting, updates and removal |
| [Use CartVerity](docs/USAGE.md) | Controls, settings, metrics and results |
| [Set up references](docs/REFERENCES.md) | DAT import, source details and per-game hashes |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Boot, display, SD and reference problems |
| [Log format](docs/LOG_FORMAT.md) | Saved reports and partial scans |
| [Limits](docs/LIMITATIONS.md) | Caching, interpretation and hardware boundaries |
| [Build and license](native/README.md) | Firmware build and complete GPL source |
| [Testing](docs/TESTING.md) | Automated checks and hardware reports |

## Development and license

The firmware is based on pinned **GodMode9 2.2.3**. [Source notes](docs/SOURCES.md)
· [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md).
This branch contains the standalone app; the obsolete `.gm9` checker and its
documentation remain recoverable in Git history.

Original CartVerity sources/tools use [MIT](LICENSE). The combined firmware is
**GPL-3.0-or-later**, with upstream notices retained. Each firmware release
includes complete corresponding source and build information. Older distributed
native versions' source is retained in a separate source archive when releases
are consolidated. CartVerity is not affiliated with Nintendo or GodMode9's maintainers.
