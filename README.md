# CartVerity

by **studioIV**

[![Native dashboard](https://github.com/studioIV/cartverity/actions/workflows/native.yml/badge.svg)](https://github.com/studioIV/cartverity/actions/workflows/native.yml)
[![Script and helper checks](https://github.com/studioIV/cartverity/actions/workflows/check.yml/badge.svg)](https://github.com/studioIV/cartverity/actions/workflows/check.yml)

A standalone Nintendo DS cartridge integrity checker for the Nintendo 3DS
family, developed for New Nintendo 3DS XL. It boots directly into a dual-screen
dashboard built from GodMode9 2.2.3. No script execution or file browser is needed.

**Current standalone release: v0.2.0-alpha.4 (experimental).**
[Download CartVerity.firm](https://github.com/studioIV/cartverity/releases/download/v0.2.0-alpha.4/CartVerity.firm)
or open the [release and checksums](https://github.com/studioIV/cartverity/releases/tag/v0.2.0-alpha.4).

## Start here

1. On an already configured Luma3DS console, copy `CartVerity.firm` to
   `SD:/luma/payloads/CartVerity.firm`. Keep your working GodMode9 payload.
2. Power off, insert an original standard Nintendo DS cartridge, then hold
   **START** while powering on and select **CartVerity**.
3. Press **A** to begin. Keep the cartridge inserted during both passes.
4. Read the result; press **X** for hashes and the saved SD report path.

Do not replace `boot.firm` or flash this payload to NAND. CartVerity does not
install custom firmware. Detailed instructions are in [installation](docs/INSTALL.md).

## Tutorials

| Guide | What it covers |
| --- | --- |
| [Tutorial index](docs/TUTORIALS.md) | Choose a task and follow it step by step |
| [Install, update and remove](docs/INSTALL.md) | SD layout, booting, replacing the payload |
| [Scan, controls and settings](docs/USAGE.md) | Progress bars, buttons, results and session settings |
| [Add a trusted reference](docs/REFERENCES.md) | Exact filenames, binary SHA-1 files and reference policies |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Boot problems, unsupported carts, flicker, references and SD errors |
| [Read the log](docs/LOG_FORMAT.md) | Native fields, completion and partial scans |
| [Limits](docs/LIMITATIONS.md) | What the checker can and cannot establish |
| [Build and source licensing](native/README.md) | Build the firmware and obtain complete GPL source |

## What the standalone app does

- Reads the full normalized DS ROM twice, reinitializing cartridge access before
  each pass. Compares whole-ROM SHA-1 and 1 MiB logical-region CRC32 values.
- Shows overall/pass progress, average MiB/s, elapsed time, ETA and changed regions.
- Renders in RAM and publishes changed pixels to reduce visible redraw flicker.
- Offers **Y-button settings** for refresh, brightness, reference policy and
  the initial result page. Settings last until power off or reboot.
- Compares per-game references or an imported database; saves unique SD text logs.
- Shows **by studioIV** on the top screen across all pages.

The native build bypasses GodMode9's save-chip capacity probe. It writes only
SD report files and does not write cartridge ROM, save memory or NAND. No ROM
dump is saved. It does not repair or refresh cartridges.

**Consistent reads without a trustworthy reference remain unverified.** A
reference mismatch can reflect a different revision or dump format. Changed
logical regions are not a map of damaged physical cells.

Standard DS cartridges up to 512 MiB are accepted. DSi-enhanced and 3DS
cartridges are rejected; special-storage/flashcart compatibility is not claimed.
See [limits and interpretation](docs/LIMITATIONS.md).

## Offline reference database

Import a user-downloaded **No-Intro Nintendo DS XML DAT** with the supplied
`tools/import_dat.py`, then put `nds.cvdb` in `SD:/gm9/support/cartverity/`.
After two consistent passes, CartVerity looks for an exact SHA-1 **and size**
match and shows `MATCHES_DATABASE` with the catalog title. Missing entries
remain unverified. Existing per-game `.nds.sha1` files take priority.

Reference metadata/hashes originate from **[No-Intro](https://no-intro.org/)**
and its **[official DAT-o-MATIC](https://datomatic.no-intro.org/)** service;
[DS DAT notes](https://wiki.no-intro.org/index.php?title=Nintendo_-_Nintendo_DS_dat_notes)
explain representation context. No real DAT/database or ROMs are bundled.
Download a compatible full decrypted/normalized DAT from the official source.
The importer records its name, version, original SHA-256 and source URL; the
app displays these on a reference-source page and records them in logs.
Attribution is recorded, not authenticated. CartVerity is not a No-Intro product.

[Import/setup tutorial](docs/REFERENCES.md) · [source and attribution](docs/REFERENCE_SOURCES.md)
· [binary database format](docs/REFERENCE_DATABASE_FORMAT.md).
The release includes a `CartVerity-reference-tools.zip` package with both
import and single-reference helpers. Python 3.10+ is needed only on the PC.

## Validation and development

The alpha.3 release passed its ARM build, compiled host scan/display/settings
tests, script/helper matrix and native initializer save-access audit. Alpha.4
adds the importer and database validation/lookup tests; see Actions for its run. Host tests
and a successful build do not certify physical hardware behavior. The user
reported native display flicker; alpha.2 introduced incremental presentation.
Confirmation of the visual improvement and a complete native hardware test
matrix remain pending. [Testing](docs/TESTING.md) and [validation records](docs/VALIDATION.md).

For contributions and hardware reports, see [CONTRIBUTING.md](CONTRIBUTING.md).
Do not upload ROMs, saves, keys or personal console identifiers.

## Legacy script

The older v0.1.0 `.gm9` checker is retained for historical compatibility.
[Legacy instructions](docs/LEGACY_SCRIPT.md) explain its separate installation,
results and limitations. Stock GodMode9 initialization can write and restore an
EEPROM save byte during capacity detection; the script cannot suppress that
probe. The standalone build explicitly bypasses it.

## License and attribution

Original CartVerity sources and helpers use the [MIT license](LICENSE).
The combined GodMode9-derived `.firm` uses **GPL-3.0-or-later**, with upstream
component notices preserved. Native releases include complete corresponding
source and build information; the small CartVerity source folder alone is not
the firmware's complete corresponding source. [Build and licensing details](native/README.md).

This project is not affiliated with Nintendo or the GodMode9 maintainers.
