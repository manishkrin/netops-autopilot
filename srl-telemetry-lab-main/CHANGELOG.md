# Changelog

All notable changes to this lab are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Grafana alerting is now provisioned from disk under `configs/grafana/alerting/`, mounted into the `grafana` container at `/etc/grafana/provisioning/alerting` (`st.clab.yml`).
- New alert rule `Leaf1 Interface Down` (folder `NetOps Alerts`, group `interface-health`) in `configs/grafana/alerting/interface-down-rules.yml`, which fires when any of leaf1's cabled interfaces (`e1-1`, `e1-49`, `e1-50`) reports `interface_oper_state == 0` (down) for 10+ seconds.
- `README.md`: new "Alerting" section documenting the provisioned alert rule, how it is scoped, and how to test it.

### Changed

- `configs/grafana/datasource.yml`: pinned a fixed `uid: PBFA97CFB590B2093` on the Prometheus datasource so provisioned alert rules can reliably reference it across lab redeploys.
