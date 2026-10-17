# Reference data sources and attribution

## No-Intro

CartVerity's XML DAT importer targets **No-Intro Nintendo DS** metadata.
No-Intro supplies preservation catalog names, versions, ROM sizes and hashes.
CartVerity, by studioIV, supplies the importer, binary format, offline lookup,
interface and logging; this is not a No-Intro product or endorsement.

- Official project: [No-Intro](https://no-intro.org/).
- Official DAT distribution: [DAT-o-MATIC](https://datomatic.no-intro.org/).
- Format/representation context: [Nintendo DS DAT notes](https://wiki.no-intro.org/index.php?title=Nintendo_-_Nintendo_DS_dat_notes).

Download a Nintendo DS XML DAT whose digests correspond to the full decrypted/
normalized representation used by GodMode9. An encrypted or trimmed hash is not
interchangeable. A generic DAT name alone does not prove compatible bytes.
The importer requires an explicit representation acknowledgement, but does not
convert or inspect ROMs. Real-cartridge/database compatibility still needs
physical validation.

## Recorded provenance

Every imported `.cvdb` embeds the DAT's name, version, original file SHA-256,
No-Intro attribution and the official DAT-o-MATIC source URL. The standalone
app displays these on its reference-source page and writes them to scan logs,
along with any matched entry title. The full title/name may be longer than a
screen line; logs retain the stored values.

This metadata records the input's claimed source, not an authenticated download
or signature. A third party can alter a DAT or its author field. The database's
CRC32 detects accidental damage; it does not authenticate No-Intro. Obtain your
input from the official source and retain the original DAT for audit.

## Distribution boundaries

No No-Intro DAT, real reference database or ROM content is bundled in this
release. The official DAT download endpoint was unavailable to this development
session; automated tests use clearly synthetic records. Users import their own
download with the supplied tool. No website access control is bypassed.

CartVerity's MIT license covers its original code and tools; it does not relicense
No-Intro's catalog data or imply that studioIV authored it. Preserve source
attribution and observe the source's terms when sharing imported data. The
combined firmware's GPL source requirements remain separate.

## User-supplied sidecars

A per-game `.nds.sha1` file has no embedded provenance. The app labels it as a
user-supplied sidecar. Keep a separate note identifying where its expected hash
came from. A hash from the same cartridge being tested is a personal baseline,
not an independent known-good reference. [Setup tutorial](REFERENCES.md).
