# Contributing

Start with the [README](README.md), [limits](docs/LIMITATIONS.md) and
[native build](native/README.md). Keep cartridge ROM, saves and NAND read-only.
Preserve the initializer's save-probe bypass and preprocessed-code audit. SD
writes need a documented purpose and checked outcomes. Do not promote observed
hashes automatically into trusted references.

Run the applicable [tests](docs/TESTING.md), including a real ARM build for
native changes. Update controls, reference semantics and log documentation when
their contract changes. Keep complete GPL corresponding source available for
each distributed firmware and preserve upstream notices.

Hardware reports should include exact app version, console model, cartridge
code/region/revision, settings and a redacted native text log. For display
issues describe flashing versus tearing and the refresh interval. Distinguish
personal baselines from independently sourced hashes. Do not attach ROMs,
saves, keys, private console identifiers or catalogs you cannot redistribute.
