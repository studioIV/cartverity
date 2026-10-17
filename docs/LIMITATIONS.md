# Standalone scope and limitations

## Cartridge support

The native app accepts standard DS cartridges up to 512 MiB with a standard
DS header. It rejects 3DS and DSi-enhanced cartridges. Special-storage titles,
flashcarts and unusual hardware are not validated. New 3DS XL is the development
target; broader model compatibility requires testing.

## Read-only integration

The dedicated entrypoint bypasses the GodMode9 browser. Its initializer skips
save-detection blocks, including the upstream EEPROM write/restore capacity
probe. The app never accesses save memory and has no cart/NAND repair, write,
refresh or installation action. Only SD log directories/files are created or
written. Settings are session-only and have no SD configuration file.

The old `.gm9` script cannot suppress stock GodMode9's initialization probe;
see [legacy limitations](LEGACY_LIMITATIONS.md). Its write scope must not be
confused with the native integration's bypass.

## What the scan measures

Two SHA-1 passes cover the full normalized DS ROM length, including padding.
The secure area is decrypted by GodMode9. Header/secure-area buffers are cached;
reinitializing before each pass reacquires them but is not a physical-cell or
electrical diagnostic. CRC32 identifies differing 1 MiB logical regions; matching
CRC32 regions alone do not establish correctness. Whole SHA-1 is also compared.

GodMode9's low-level DS read interface lacks comprehensive per-sector status.
The adapter detects removal, identity/initialization errors and reported read
failures, but cannot independently prove the byte count of every bus transfer.
The portable scan core's short-read rejection does not remove that boundary.
Cancellation requires the active cartridge operation to return.

## Reference interpretation

Consistent repeated reads can include stable corruption. A match means agreement
with the supplied digest, not authenticated provenance. A mismatch can mean a
different region/revision, length, padding, secure-area representation or wrong
reference, as well as differing cartridge data. SHA-1 provides archival
compatibility, not adversarial authenticity. No online lookup or DAT/database
import exists in this release. [Reference instructions](REFERENCES.md).

## Display, logging and validation

Incremental presentation avoids repeated visible full-screen clears; it does
not perform hardware VBlank page flipping. Remaining tearing/flicker needs
physical testing. Speed is an average including initialization/UI overhead;
ETA is an estimate. Changing refresh never changes the two full passes.

SD writes are checked, synced and closed but are not atomic transactions.
Power loss or storage faults can damage a report even if a completion marker
is readable. A completed report can record a failed/cancelled scan.

Host tests, build success and a host preview cannot certify console behavior.
The initial user-provided complete log validated the old script on one cart;
native observations and pending checks are recorded in [testing](TESTING.md).
The app cannot assess remaining cartridge lifespan or repair damaged hardware.
