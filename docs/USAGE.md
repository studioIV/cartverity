# Scanning, controls and settings

## Run a scan

1. [Boot the standalone app](INSTALL.md) with an original standard DS cartridge
   inserted. Use a charged console or external power for long scans.
2. Read the ready screen. If a reference is required or invalid, resolve the
   message before starting; [reference instructions](REFERENCES.md).
3. Press **A**. CartVerity creates an SD report, then reads the full normalized
   ROM twice. It reinitializes cartridge access before each pass.
4. Leave the cartridge and SD inserted. **B** cancels after the current cartridge
   operation returns. A cancelled scan is recorded as cancelled, not passed.
5. Read the result. **X** cycles summary, SHA-1, SD report and reference-source pages.

No ROM dump is saved. No repair or cartridge refresh operation is performed.

## Controls

| Screen | Button | Action |
| --- | --- | --- |
| Ready | A | Start a scan |
| Scan | B | Request cancellation |
| Result | X | Cycle detail pages |
| Result | A | Return to discovery/ready; press A again to scan |
| Ready, error or result | Y | Open settings; returning rediscovers the cartridge |
| Main dashboard outside a scan | B | Power off |
| Main dashboard outside a scan | START | Reboot |
| Settings | Up / Down | Select a row |
| Settings | Left / Right, or A | Change the selected value |
| Settings | X | Restore defaults |
| Settings | B or Y | Return to discovery/ready |

Buttons held while leaving a screen must be released before the next action.
Controls on the settings screen take precedence over dashboard power controls.

## Dashboard metrics

| Metric | Meaning |
| --- | --- |
| Overall | Completed bytes across both full passes |
| Pass | Progress through the current pass |
| Read MiB | Bytes read in this pass, displayed in whole MiB |
| MiB/s | Average across the scan, including initialization and UI overhead |
| ETA | Estimate from elapsed time and completed bytes; not a deadline |
| Elapsed | Scan time, excluding pre-scan menus |
| Regions | 1 MiB logical regions compared during pass two |
| Changed | Regions whose CRC32 differs between passes |

A zero changed-region count alone is not a correctness verdict. Whole-ROM
SHA-1 is also compared. Regions refer to ROM offsets, not physical chip cells.

## Session settings

Press **Y** outside a scan. Changes apply until power off or reboot; they are
not saved to the SD. Returning from settings clears the displayed result and
rediscovers the cartridge; completed SD reports are retained.

| Setting | Choices | Default |
| --- | --- | --- |
| Refresh | 100, 250, 500, 1000 ms | 250 ms |
| Brightness | Auto, Low, Medium, High, Maximum | Medium |
| Reference | Auto (sidecar, then database), Require input, Ignore both | Auto |
| Result page | Summary, SHA-1, SD report | Summary |

Refresh controls UI update frequency, not read coverage. Cancellation is checked
at normal block boundaries regardless of this setting. Higher intervals can
reduce visible updates. Auto brightness uses the upstream brightness API.
Reference policies are explained in [the reference tutorial](REFERENCES.md).
All settings keep two full passes; there is no abbreviated quick-pass mode.

## Understand the result

| Screen / log result | Meaning |
| --- | --- |
| READS CONSISTENT / `CONSISTENT_UNVERIFIED` | Both reads agree; no matching independent reference was established |
| REFERENCE MATCH / `MATCHES_SUPPLIED_REFERENCE` | Both reads agree with the supplied hash; its source is not authenticated |
| DATABASE MATCH / `MATCHES_DATABASE` | Both reads agree with a database SHA-1 and size; source details and logs record DAT provenance |
| REFERENCE DIFFERS / `REFERENCE_MISMATCH` | Reads agree with each other but differ from the supplied hash |
| READS DIFFER / `INCONSISTENT_READS` | Whole hashes or logical-region comparisons disagree |
| SCAN CANCELLED / `CANCELLED` | The user cancelled; progress may be partial |
| SCAN INCOMPLETE / `READ_ERROR` | Initialization, identity check or reported read failed |
| SCAN INCOMPLETE / `SHORT_READ` | The scan core received fewer/more bytes than requested |
| SCAN INCOMPLETE / `INVALID_INPUT` | Internal scan inputs were invalid; report the log/version |
| CANNOT START | Discovery, reference or log setup prevented a scan |

A valid database with no exact entry leaves `CONSISTENT_UNVERIFIED` and records
`database_result=NO_MATCH`. This does not mean the cartridge is damaged. Require
allows a loaded valid database but cannot guarantee that it contains your game.
Sidecars take priority; Ignore skips both inputs. [Reference setup](REFERENCES.md).

The native DS adapter cannot measure every underlying bus transfer's length;
`SHORT_READ` handling in the core does not imply complete hardware fault detection.
An SD log failure is separate from the ROM result: the report may be partial even
if a result is displayed. See [limits](LIMITATIONS.md) and [troubleshooting](TROUBLESHOOTING.md).

## Scan again or check another cartridge

For the same cartridge, press A at the result to return to ready, then A to scan.
For another cartridge, power off first, exchange it, and boot the app again.
Keep the card inserted through both passes. Never remove the SD during writes.
