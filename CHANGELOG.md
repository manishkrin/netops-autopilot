# Changelog

All notable changes to NetOps Autopilot are documented in this file. Changes to the telemetry lab are tracked in [srl-telemetry-lab-main/CHANGELOG.md](srl-telemetry-lab-main/CHANGELOG.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Simulator alerts now carry `peer_device`, `peer_interface`, `failure_mode` (`link-down`, `admin-disable`, `optic-failure`, `peer-reboot`, or `recovered`), and `lab` attributes.
- Docstring for `generate_alerts()`.
- `CHANGELOG.md`.

### Changed

- The simulator picks a random device and interface from the srl-telemetry-lab topology (`spine1`/`spine2`, `leaf1`–`leaf3`, `client1`–`client3`) instead of the fixed `router-edge-01` / `GigabitEthernet0/1`. Each down/up pair shares one link and failure mode, and choices are seeded from the run ID.
- `examples/interface-flap-alert.json` now describes a lab link (`spine2` `e1-1`, peer `leaf1` `e1-50`) with `source: netops-simulator`.
- `README.md` rewritten as a short introduction plus numbered steps to reproduce the demo, linking to the telemetry lab README for container lab setup.
- `AGENTS.md` and `docs/project-brief.md` updated to reflect the lab-based simulator.
