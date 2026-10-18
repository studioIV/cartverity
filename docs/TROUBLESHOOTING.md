# Standalone troubleshooting

## CartVerity is missing from the boot menu

Check `SD:/luma/payloads/CartVerity.firm`, not `gm9/scripts`, a ZIP file or
`CartVerity.firm.firm`. Hold START while powering on with your configured Luma
setup. Keep the existing GodMode9 payload. [Install guide](INSTALL.md).

## The upper screen shows script code

You launched the legacy `.gm9` checker in GodMode9. Boot the standalone
`CartVerity.firm` from the payload menu. The standalone app starts directly in
its dashboard; no script or Lua file is required.

## An old version or no settings menu appears

Replace the actual payload you selected, and check for duplicate versions in
`luma/payloads`. Alpha.2 added Y settings and incremental redraws; alpha.3 adds
`by studioIV`. Settings only open outside a scan.

## Flicker or tearing remains

Alpha.2+ renders in RAM and publishes changed pixels; it does not use hardware
VBlank page flipping. In Y settings, try 500 or 1000 ms refresh. This changes
display updates only. Report version, console model, refresh and whether it is
full-screen flashing, moving bars, or text tearing. A short display video can
help; avoid including personal files. The host preview is not a hardware test.

## Tapping a control label does nothing

The footer badges identify the console's physical buttons. Press the labeled
button; CartVerity does not use touch input. [Controls](USAGE.md#controls).

## Requires a standard DS cartridge / initialization failed

The app accepts standard DS ROM cartridges up to 512 MiB and rejects
DSi-enhanced and 3DS carts. Special-storage carts and flashcarts are not validated.
Power off, confirm the cartridge is seated and reboot. The message does not
prove a hardware defect. Never exchange cartridges during a scan.

## A reference is required / reference must be 20 binary bytes

Check Y settings and the exact `reference_path=` from a previous native log.
Use [the helper tutorial](REFERENCES.md) to create binary data. With Auto or
Require, a malformed/unreadable file blocks scanning. Ignore deliberately skips
the file and produces unverified results; it does not fix the reference.

## CONSISTENT_UNVERIFIED

Both reads agreed, but no reference match was established. This is expected
without reference input, with Ignore selected, or when a database has no exact
SHA-1-and-size match. It is neither proof of corruption nor a
known-good verdict. [Reference tutorial](REFERENCES.md).

## REFERENCE_MISMATCH or INCONSISTENT_READS

For a mismatch, confirm reference provenance, region/revision, length and dump
representation. For differing reads, retain the log and retry after powering
off/rebooting. Contacts, reader behavior and cartridge data can all matter;
the result does not isolate the cause. There is no repair button.

## Cannot create a log / SD LOG FAILED

Check that the SD is readable, writable and has free space. A reader's write-lock
tab may matter when preparing files on a computer. Do not remove the console SD
during a scan. Pre-scan log setup failures prevent scanning. Later failures may
leave a result on-screen with an incomplete report. Keep any partial report;
`state=COMPLETE` is a report marker, not an atomic guarantee against SD faults.

## Cancel seems delayed / settings disappear after reboot

B cancellation waits for the current cartridge operation to return. There is no
fixed cancellation time if hardware does not return. Settings are intentionally
session-only in the current release; no persistent configuration file is written.

## Report a problem

Include app version, console model, cartridge code/revision if known, relevant
settings, expected/observed behavior and a redacted native text log. Include the exact displayed version. Do not attach ROMs, saves,
keys or console serials. [Testing checklist](TESTING.md).

## Database invalid, not found or no match

CartVerity reads `SD:/gm9/support/cartverity/nds.cvdb`, not a DAT/ZIP placed directly
on the SD. Run [the importer](REFERENCES.md) first, use Auto or Require, and
remember a per-game sidecar takes priority. Ignore skips both sources.

Invalid size, metadata, CRC or record ordering blocks the scan. Recreate the
database from your retained official DAT; do not edit binary bytes manually.
A different existing output is preserved by the importer: back it up before
replacing it. A valid database with no SHA-1-and-size match is still unverified,
not a damaged-cartridge verdict. Check dump representation and catalog coverage.

No-Intro is the catalog source; CartVerity does not bundle real catalog data or
authenticate imported provenance. [Source attribution](REFERENCE_SOURCES.md).
