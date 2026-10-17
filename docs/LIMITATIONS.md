# Supported limits

## What is measured

The SHA-1 calculations cover the full standard `.nds` virtual file exposed by GodMode9, including its padding. They do not read save data. The standard view uses a decrypted secure area. The `.trim.nds` and `.nds.enc` views contain different byte sequences and need different references.

GodMode9 initializes and caches parts of the cartridge. Header and secure-area bytes, and relevant DSi modcrypt data, can be returned from cached buffers. Calculating a digest twice does not force those bytes to be physically read twice. A power cycle and fresh run can provide an additional observation, but still does not turn this into a complete electrical diagnostic.

## What failure means

`shaget` exposes success or failure to a `.gm9` script. It does not provide a structured distinction between cancellation, file-read failure, and other hash failures. This project deliberately combines them as `FAILED_OR_CANCELLED` and never declares the cartridge damaged solely because a command failed.

GodMode9's ordinary NTR cartridge read path does not provide the script with a per-sector error report. Its file-hash function also does not independently assert that every read returned the requested byte count. These are upstream boundaries. This script cannot guarantee detection of all low-level faults, identify a failing chip or sector, reset the cartridge reader, bypass its caches, or repair data.

GodMode9's `verify` command dispatch has no standalone NDS verification branch in the pinned release. Calling that command would not add a supported whole-ROM integrity check, so the script uses hashes instead.

## References and interpretation

A match establishes agreement with supplied bytes, subject to the behavior above. The user supplies and trusts the reference. No provenance authentication, online database lookup, or automated game identification against a database is performed.

A mismatch can result from the wrong revision, region, representation, length, or reference, as well as differing cartridge data. Stable corruption can produce matching repeated reads. SHA-1 is used for compatibility with preservation references and accidental-difference detection, not as a defense against deliberately constructed cryptographic collisions.

The desktop helper strictly creates a 20-byte binary reference. On the console the script requires a successful 20-byte read and rejects a successfully read byte after it. The EOF probe cannot distinguish end-of-file from an SD read failure, so exact reference length cannot be proven during storage faults. A missing/inaccessible reference can likewise appear absent. The reported status must not be treated as authentication of the SD card or its contents.

## Files, compatibility and privacy

All script write destinations are SD log paths. The script has no `allow`, `cp`, `rm`, `inject`, `fill`, `fset`, `encrypt`, `decrypt`, `install`, or repair command. It relies on normal GodMode9 cartridge initialization; inspecting a cartridge still sends read/protocol commands to its controller.

Logs contain version, console family, timestamps, ROM path, header identifiers, hashes, and results. They omit console serials, unique keys, ROM payloads, and saves. A filename can reveal the game being checked. This project includes no cartridge data or actual game reference database.

The supported target is official GodMode9 2.2.3 on New 3DS XL, pending hardware confirmation. A fork, older version, unusual DS cartridge, flashcart, DSi-enhanced title, or special storage cartridge requires its own testing. There is no special support for WarioWare D.I.Y., NAND-backed cartridge storage, or flashcarts. A full `.nds` view being available does not establish that every cartridge-specific feature is represented.

GodMode9 treats the last `@` in a hash source argument as its offset/size separator. The script appends an explicit `@0` to retain any `@` inside the filename and hash the full view. Periods in titles are also retained.

## Logging and testing

Each run chooses an unused log path. A write failure stops the script, preserving whatever was written so far. Final fields are appended after hashing; the last state is authoritative for a normal readable log. Appending text/newlines and storage flushes are not atomic. Power loss or SD failure can leave a truncated or misleading final line, so the completion marker is not a transaction guarantee.

Local and CI tests validate the script's modeled behavior and its source-supported command signatures. They do not constitute execution in GodMode9 or a hardware guarantee. See [TESTING.md](TESTING.md) for the remaining validation work.
# Stock GodMode9 initialization caveat

The script itself contains no cartridge/save write commands. However, pinned
GodMode9's `InitCartRead` calls `CardSPIGetCardSPIType`; for some EEPROMs its
`_SPIIsDataMirrored` routine writes a complemented save byte and restores it to
detect capacity. Therefore the stock `.gm9` path cannot guarantee that save
memory is never written. CartVerity's native build conditionally removes the
initializer's save-detection blocks and does not access save memory.

