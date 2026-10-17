# CartVerity

by **studioIV**

[![Native dashboard](https://github.com/studioIV/cartverity/actions/workflows/native.yml/badge.svg)](https://github.com/studioIV/cartverity/actions/workflows/native.yml)
[![Script and helper checks](https://github.com/studioIV/cartverity/actions/workflows/check.yml/badge.svg)](https://github.com/studioIV/cartverity/actions/workflows/check.yml)

A standalone Nintendo DS cartridge integrity checker for the Nintendo 3DS
family, developed for New Nintendo 3DS XL. It boots directly into a dual-screen
dashboard built from GodMode9 2.2.3. No script execution or file browser is needed.

**Current standalone release: v0.2.0-alpha.3 (experimental).**
[Download CartVerity.firm](https://github.com/studioIV/cartverity/releases/download/v0.2.0-alpha.3/CartVerity.firm)
or open the [release and checksums](https://github.com/studioIV/cartverity/releases/tag/v0.2.0-alpha.3).

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
- Optionally compares a supplied per-game reference; saves unique SD text logs.
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

## References available today

The app loads one 20-byte binary `.nds.sha1` sidecar per cartridge from
`SD:/gm9/support/dscheck/`. The desktop helper creates that file from a SHA-1
you supply. [Follow the reference tutorial](docs/REFERENCES.md).

Automatic database lookup, DAT importing and a bundled known-good hash database
are **not implemented**. A personal baseline records an observation; it is not
independent proof that a cartridge is correct.

## Validation and development

The current release passed its ARM build, compiled host scan/display/settings
tests, script/helper matrix and native initializer save-access audit. Host tests
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
