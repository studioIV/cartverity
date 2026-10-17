# Legacy v0.1.0 GodMode9 script

The recommended current path is the [standalone CartVerity app](../README.md).
This page describes the older `.gm9` implementation only.

**Read-only caveat:** the script has no cart/save-write commands, but stock
GodMode9's NDS initializer can write and restore an EEPROM byte during save
capacity detection. A script cannot prevent it. The native build bypasses
save-chip detection entirely.

## Install and run the old script

1. Use official GodMode9 2.2.3 on an already configured console.
2. Copy `gm9/scripts/CartVerity.gm9` to `SD:/gm9/scripts/CartVerity.gm9`.
3. Power off, insert the DS cartridge, then boot GodMode9.
4. Select the script, press A and choose Execute GM9 Script. Accept its prompts.
5. Leave the cart inserted during both SHA-1 calculations; B cancels progress.
6. Read the result and text log under `SD:/gm9/out/dscheck/`.

The source preview on the upper screen and generic script completion dialog
belong to this older interface. It has no native Y settings, incremental
dashboard or per-pass cartridge reinitialization.

The legacy [v0.1.0 release](https://github.com/studioIV/cartverity/releases/tag/v0.1.0)
is retained. It is not the standalone `.firm` release.

## Results and references

The script uses `rom=`, `read_result=`, `reference_result=` and `result=` fields.
Its READ_INCOMPLETE status combines failed/cancelled hash commands. Discovery
can produce NO_DS_ROM, FULL_ROM_UNAVAILABLE or HEADER_READ_FAILED.

Both implementations use the same per-game 20-byte binary reference files and
desktop helper. Unlike native Auto/Require, an invalid reference is reported as
INVALID_OR_UNREADABLE while the old script can continue hashing. Its LOADED
state means the reference was readable but not necessarily compared.

See [legacy log fields](LEGACY_LOG_FORMAT.md) and
[legacy limits](LEGACY_LIMITATIONS.md). A user-provided log confirmed one N3DS,
GodMode9 v2.2.3 run with matching reads, no reference and a complete report. That
does not validate the native payload or other games/models.
