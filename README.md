# NetOps Autopilot

NetOps Autopilot ingests network alerts, stores each event once, and exposes them through an API. This demo shows the first slice end to end:

- A simulator generates synthetic interface-flap alerts for random links of the Nokia SR Linux [telemetry lab](srl-telemetry-lab-main/README.md) topology (`spine1`/`spine2`, `leaf1`–`leaf3`, `client1`–`client3`).
- The FastAPI service validates each alert, stores it in SQLite, and treats a repeated `event_id` as a duplicate.
- Optionally, a real interface failure in the containerlab fabric is forwarded by Grafana to the same API.

The demo is safe to run locally: it uses synthetic data and never changes network devices.

## Recommended VM (macOS): OrbStack with Debian 12

For a consistent Linux environment on macOS, use [OrbStack](https://orbstack.dev/) with Debian GNU/Linux 12 (bookworm). This setup is optional; you can also run the demo directly on macOS or Linux.

Install OrbStack with Homebrew and launch the app once to complete setup:

```bash
brew install --cask orbstack
```

Then create and enter a Debian machine from a macOS terminal:

```bash
orb create debian:bookworm clab
orb -m clab
```

Confirm the machine is running Debian 12:

```bash
cat /etc/os-release
```

Inside the VM, install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/), add uv to the current shell's `PATH`, and install the Python version required by this project:

```bash
sudo apt update
sudo apt install -y git
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv python install 3.12
```

To run the container lab on Debian, install Containerlab and its Docker runtime. Containerlab's [official quick setup script](https://containerlab.dev/install/) installs Docker Engine, Docker Compose, Containerlab, and the GitHub CLI together:

```bash
export SETUP_SSHD="false"
curl -sL https://containerlab.dev/setup | sudo -E bash -s "all"
```

The script also changes SSH server settings by default; `SETUP_SSHD="false"` disables that change. After installation, run `newgrp docker` or log out and back in to use Docker without `sudo`.

Then continue with the clone and install steps below from inside the VM. Docker and Containerlab are only needed for the optional lab steps.

## Recommended environment (Windows): WSL 2

On Windows 10 (version 2004 or newer) or Windows 11, [WSL 2](https://learn.microsoft.com/en-us/windows/wsl/install) provides a lightweight Linux environment, so a separate VM application is not needed. In an Administrator PowerShell, install WSL with Debian and restart if prompted:

```powershell
wsl --install -d Debian
```

Open Debian from the Start menu to finish its initial setup, then run the remaining commands from its terminal. Install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/), add uv to the current shell's `PATH`, and install Python 3.12:

```bash
sudo apt update
sudo apt install -y git
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv python install 3.12
```

The WSL Debian image may use a newer release than Debian 12 (bookworm); check with `cat /etc/os-release` if the exact release matters. Keep the project files in the Linux filesystem (for example, under `~/`) for the best development experience. Docker and Containerlab are only needed for the optional lab steps.

For the optional containerlab lab, use [Docker Desktop's WSL 2 integration](https://docs.docker.com/desktop/features/wsl/) and follow the [Containerlab on Windows guide](https://containerlab.dev/windows/). Avoid installing a separate Docker Engine inside the WSL distribution when using Docker Desktop integration.

## Reproduce the demo

### 1. Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/)
- Git
- Optional: Docker with the Compose plugin for the database web UI (step 6); Containerlab for the lab (steps 7–8). On Debian, the Containerlab setup above installs Docker and Compose as well.

Docker is not required for the API and simulator demo. The database web UI requires Docker and the Compose plugin to be running in your environment. For a Debian VM, the Containerlab setup above installs them; for OrbStack's macOS Docker engine, see its [Docker documentation](https://docs.orbstack.dev/docker/). For WSL, use [Docker Desktop's WSL 2 integration](https://docs.docker.com/desktop/features/wsl/). To run the lab on WSL, also follow the [Containerlab on Windows guide](https://containerlab.dev/windows/).

### 2. Clone and install

If the repository is private, make sure your GitHub account has access. When Git prompts for credentials, enter your GitHub username and a personal access token with read access to this repository as the password; GitHub account passwords are not accepted. For a fine-grained token, grant access only to this repository and set **Contents** to **Read-only**. Do not put the token in the clone URL or share it.

```bash
git clone https://github.com/manishkrin/netops-autopilot.git
cd netops-autopilot
uv sync --extra dev
```

#### Optional: concise Bash prompt

From the repository root, add the prompt script to your Bash startup file and load it in the current shell:

```bash
printf 'source "%s/netops-prompt.sh"\n' "$PWD" >> ~/.bashrc
source ~/.bashrc
```

Add the `source` line only once. The prompt shows `../netops-autopilot/` at the repository root and keeps the relative subdirectory while you move around inside the repository, for example `../netops-autopilot/srl-telemetry-lab-main`. Outside this repository it displays the full working-directory path. The `[clab]` label is fixed in [netops-prompt.sh](netops-prompt.sh); edit `PS1` there to customize it.

### 3. Run the self-contained check

Starts the API on a free port with a throwaway database, sends 25 alerts (every fifth replayed), and exits non-zero unless exactly 20 were stored.

```bash
uv run python scripts/demo.py
```

### 4. Start the API

```bash
uv run uvicorn netops_autopilot.api:app --reload
```

Interactive docs: <http://127.0.0.1:8000/docs>.

### 5. Send simulated alerts

In a second terminal:

```bash
uv run netops-simulator --count 25 --duplicate-every 5
```

Expected summary: `{"submitted": 25, "accepted": 20, "duplicates": 5, "failed": 0}`.

### 6. Inspect the results

```bash
curl http://127.0.0.1:8000/v1/metrics
curl 'http://127.0.0.1:8000/v1/alerts?device=spine1&event_type=interface_flap&limit=10'
curl -X POST http://127.0.0.1:8000/v1/alerts \
  -H 'content-type: application/json' \
  --data @examples/interface-flap-alert.json
```

Alerts are stored in `var/netops-autopilot.db`. Optionally, to browse the database in a web UI (requires Docker and the Compose plugin), run `docker compose up -d` and open <http://127.0.0.1:8080>. You can skip this and use the API commands above without affecting the demo.

### 7. Setting up container lab

Follow the [telemetry lab README](srl-telemetry-lab-main/README.md) to deploy the SR Linux fabric with gNMIc, Prometheus, and Grafana (`sudo containerlab deploy --reconfigure` from `srl-telemetry-lab-main/`).

### 8. Forward a real interface failure

1. Restart the API so the lab can reach it: `uv run uvicorn netops_autopilot.api:app --host 0.0.0.0 --port 8000`.
2. Check that the `st` network gateway (`docker network inspect st --format '{{(index .IPAM.Config 0).Gateway}}'`) matches the webhook URL in `srl-telemetry-lab-main/configs/grafana/alerting/contact-points.yml` (default `172.80.80.1`).
3. Admin-disable `ethernet-1/49` on `leaf1`, as described in the lab README's [alerting section](srl-telemetry-lab-main/README.md#alerting).
4. When the Grafana rule fires, the alert appears at `GET /v1/alerts`. Re-enabling the interface ingests the `resolved` event.
5. Clean up with `sudo containerlab destroy --cleanup`.

This Grafana-to-API path has not been verified end to end against a running lab.

## Development

```bash
uv run ruff check .
uv run pytest --cov --cov-report=term-missing
```

## License

[MIT](LICENSE)
