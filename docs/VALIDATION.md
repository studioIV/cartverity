# Initial validation record

Version: 0.1.0. Date: 2026-10-18.

Local environment: Windows, Python 3.11. Checks were run from the project root.

| Check | Observed result |
| --- | --- |
| `python tools/gm9check.py gm9/scripts/CartVerity.gm9` | Passed: 101 command lines and 2 labels |
| `python -m unittest discover -s tests -q` | 98 tests: 97 passed, 1 skipped |
| `python tools/check_upstream.py --source-dir <reviewed-source-cache>` | Passed: 5 source hashes and 15 command signatures |

The skipped test needs Windows symlink creation privileges. It is a desktop-helper edge-case test, not a skipped cartridge test. The full suite comprises 78 script static/scenario tests and 20 desktop-helper tests. Some tests contain multiple failure-injection cases.

The reviewed source bytes also matched their official Git blob identities at commit `0ee81b7738401b3e9f0b92b3b11159936222e542`. No upstream source is bundled in the release.

The GitHub Actions workflow is included but has not been run in this project on GitHub. Automated checks do not substitute for executing the script in GodMode9. All physical-console checks in [TESTING.md](TESTING.md) remain pending.
