# Add references to the standalone app

CartVerity supports offline lookup in an imported No-Intro Nintendo DS
XML DAT, as well as per-game binary SHA-1 sidecars. No ROM files are needed to
import a DAT. The app does not download data over the network.

## Source and attribution

Reference catalog metadata/hashes come from **No-Intro**, distributed through
[official DAT-o-MATIC](https://datomatic.no-intro.org/). See the
[No-Intro DS DAT notes](https://wiki.no-intro.org/index.php?title=Nintendo_-_Nintendo_DS_dat_notes)
for representation context and [source/attribution details](REFERENCE_SOURCES.md).
CartVerity's importer and UI are by studioIV; No-Intro is not affiliated with this app.

No real DAT/database is bundled. Download your own compatible DAT from the
official site. The original input's name, version, SHA-256 and source URL are
preserved in the database, source details screen and scan report. These record
claimed provenance; they do not authenticate the input.

## Import a database

1. Download a **Nintendo DS Logiqx XML DAT** from DAT-o-MATIC and extract it if
   compressed. Choose hashes compatible with full decrypted/normalized DS ROMs.
   Do not use encrypted, trimmed, Download Play or DSi digital data.
2. Download `CartVerity-reference-tools.zip` from the
   [alpha.5 release](https://github.com/studioIV/cartverity/releases/tag/v0.2.0-alpha.5)
   and extract it. Alternatively use the repository's tools folder.
3. With Python 3.10+ on your computer, run the command below from the extracted
   folder. Replace the DAT path and SD drive letter with your actual paths.

```text
python tools/import_dat.py --dat "C:/Downloads/Nintendo DS Decrypted.dat" --representation full-standard-nds --out E:/gm9/support/cartverity/nds.cvdb
```

The representation flag is your acknowledgement that these hashes correspond
to the full normalized view. It does not convert ROMs or infer compatibility
from an ambiguous DAT name. An explicitly encrypted system name is rejected.
Real database/known-cartridge agreement still needs physical confirmation.

The importer reads XML metadata only, records the original DAT SHA-256, sorts
and deduplicates SHA-1/size keys, and creates:

```text
SD:/gm9/support/cartverity/nds.cvdb
```

It skips explicitly bad/undumped, non-NDS and unsupported-length entries; its
output reports imported/skipped counts. Invalid dumped-entry digests fail the
import. Output is created exclusively: an identical file is accepted, while a
different existing file is never overwritten. Back up an old database before
replacing it. Retain the original DAT to audit its recorded checksum.

4. Safely eject the SD, boot the **alpha.4 or later** payload and use Auto or
   Require reference policy. Without a per-game sidecar, the dashboard should
   show `Reference: database`. A malformed database blocks the scan rather than
   silently being treated as a usable reference.
5. After both passes, inspect the result. Press X through Summary, SHA-1, SD
   report and **Reference source** pages. The source page includes the original
   DAT version/checksum and any matched title; the log retains stored metadata.

## Lookup and priority

A lookup requires the **whole-ROM SHA-1 and size** after two consistent reads.
It does not guess the expected digest from a title, region or revision label.

| Outcome | Native result |
| --- | --- |
| Exact database hash and size match | `MATCHES_DATABASE` / DATABASE MATCH |
| No matching database entry | `CONSISTENT_UNVERIFIED`, database_result=NO_MATCH |
| Cancelled, failed or differing reads | Scan outcome takes priority; database_result=NOT_COMPARED |

No database match is not evidence of damage: the catalog may be incomplete or
use different bytes. A database does not provide an independent expected entry
before scanning, so its absence never produces REFERENCE_MISMATCH.

Per-game sidecars take priority over the database. If the exact sidecar exists,
its validation/comparison is used and the database is not loaded. An invalid
sidecar blocks Auto/Require even if a database exists. Ignore skips both sources.

## Create a per-game sidecar instead

A sidecar specifies one exact expected SHA-1. It remains useful for an
independently verified reference or personal baseline.

1. With Auto selected, complete a scan and open its `native_*.txt` log on a PC.
2. Find `reference_path=`. It gives the exact candidate filename, for example:

```text
0:/gm9/support/dscheck/YU-GI-OH!WC7_AY7PA4_00.nds.sha1
```

Preserve that exact basename; do not derive it from the shortened dashboard title.
Use a trustworthy SHA-1 for the same full size, region/revision and normalized
secure-area bytes. Trimmed and encrypted hashes are not interchangeable.

3. Replace the example name, hash placeholder and SD drive letter:

```text
python tools/make_reference.py --name EXAMPLE_ABCD_00.nds --sha1 YOUR_TRUSTED_40_HEX_DIGITS --out E:/gm9/support/dscheck
```

The placeholder is not a valid hash. Provide exactly 40 hexadecimal characters;
the helper creates **20 binary bytes**. Do not rename a text digest to `.sha1`.
Conflicting files are preserved. Safely eject the SD and reboot the app.

Sidecars have no embedded source metadata; the source screen labels them as
user-supplied. Keep provenance separately. Agreement with a hash from the same
cartridge records a personal baseline, not independent known-good proof.

## Choose a reference policy

Press Y outside a scan, change Reference, then B to rediscover the cartridge.
The setting lasts until reboot.

| Policy | Behavior |
| --- | --- |
| Auto | Use a valid sidecar first; otherwise use a valid database; otherwise scan unverified |
| Require | Block without either a valid sidecar or valid database; a loaded database can still return NO_MATCH |
| Ignore | Do not inspect or compare sidecars/databases; consistent scans remain unverified |

Auto and Require block malformed/unreadable selected sources. Require means
reference input must be available; it does not guarantee the catalog contains
your cartridge. A sidecar mismatch also needs region/revision/format checking
before a hardware conclusion. [Database format](REFERENCE_DATABASE_FORMAT.md).
