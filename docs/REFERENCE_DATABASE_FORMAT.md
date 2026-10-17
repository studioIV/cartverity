# CartVerity reference database v1

File: `SD:/gm9/support/cartverity/nds.cvdb`. All integers are little-endian.
Maximum: 30000 records, 4800256 bytes. Only reference metadata/hashes are stored;
no ROM data. [Data sources](REFERENCE_SOURCES.md) and [import tutorial](REFERENCES.md).

## Header: 256 bytes

| Offset | Length | Field |
| --- | --- | --- |
| 0 | 8 | ASCII magic CVDB0001 |
| 8 | 4 | Record count, 1..30000 |
| 12 | 4 | Record size, exactly 160 |
| 16 | 4 | IEEE CRC32 of the complete file with these four bytes zeroed |
| 20 | 4 | Reserved flags, zero |
| 24 | 80 | Source label: No-Intro plus original DAT name |
| 104 | 48 | Original DAT version |
| 152 | 32 | SHA-256 of the original input DAT file, binary |
| 184 | 72 | Official source URL |

Text is printable ASCII, NUL-terminated and padded with zero bytes. The importer
normalizes Unicode to ASCII for the fixed console font and truncates fields to
leave a terminator. The original DAT checksum identifies the full input even
if a displayed name/version was shortened. No header fields are signatures.

## Record: 160 bytes

| Offset within record | Length | Field |
| --- | --- | --- |
| 0 | 20 | Full-ROM SHA-1, binary |
| 20 | 4 | ROM size in bytes |
| 24 | 128 | Entry title, printable ASCII with NUL/zero padding |
| 152 | 8 | Reserved, zero |

Records are strictly sorted by SHA-1 bytes then numeric size. Duplicate keys
are removed by the importer; a deterministic title is retained for aliases.
The supported size range is 512 bytes through 512 MiB, restricted to powers of
two. Unsupported lengths, non-NDS entries and explicitly bad/undumped entries
are skipped. Invalid dumped-entry hashes or sizes fail the import rather than
silently inventing reference data.

## Validation and lookup

The native app checks exact file length, bounds, metadata, flags, CRC32, record
ordering, sizes and reserved fields before lookup. It loads at most about
4.8 MB into RAM, closes the file, and retains the validated snapshot for a scan.
Per-game sidecars have priority. Ignore policy skips both sources.

After two consistent reads, a binary search requires exact SHA-1 **and size**.
A match produces MATCHES_DATABASE. No match leaves CONSISTENT_UNVERIFIED and
database_result=NO_MATCH. It does not produce REFERENCE_MISMATCH because the
database does not establish an expected entry by game code/revision beforehand.
Read failures, cancellation and differing reads take priority over lookup.

CRC32 guards accidental file damage, not malicious modification or provenance.
The adapter's underlying DS read/caching limits still apply.
