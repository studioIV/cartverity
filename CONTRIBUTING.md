# Contributing

The primary product is the standalone CartVerity `.firm`. Start with the
[tutorials](docs/TUTORIALS.md), [limits](docs/LIMITATIONS.md) and
[native build](native/README.md). The v0.1.0 script remains a legacy component.

Keep cartridge ROM, save memory and NAND read-only. Preserve the native
initializer's save-probe bypass and preprocessed-code audit. New SD writes must
have an explicit documented purpose and checked outcomes. Do not add repair,
refresh, permission unlocks, installations or automatic promotion of observed
hashes into trusted references.

Run applicable [automated checks](docs/TESTING.md). Native changes must compile
with the pinned GodMode9 base. Document controls, settings, reference behavior,
log fields and failure outcomes when they change. Preserve complete GPL
corresponding-source distribution with every combined firmware binary.

For script changes, use the static/model checks and keep its source ASCII/LF.
The script model does not certify native C or hardware. Update the appropriate
legacy docs rather than mixing the two products' statuses and controls.

Hardware reports should identify standalone versus legacy, exact app/base
version, console model, cartridge code/region/revision, settings, expected and
observed behavior, and a redacted text report. For display issues specify
refresh interval and flashing versus tearing. Distinguish personal baselines
from independent references with provenance. Do not attach ROMs, saves, keys,
databases you cannot redistribute or personal console identifiers.
