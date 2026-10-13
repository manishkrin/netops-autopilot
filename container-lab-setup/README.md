# Containerlab setup (SR Linux 2-node lab)

This folder contains a small [containerlab](https://containerlab.dev/) topology that spins up **two Nokia SR Linux** nodes connected back-to-back.

Topology file: `srl02.clab.yml`  
Startup configs: `srl1.cfg`, `srl2.cfg`

## Prerequisites

1. Docker (or Docker Desktop) running locally.
2. `containerlab` installed.

### Install containerlab

If you already installed containerlab, skip this.

Recommended (official quick setup):

```bash
curl -sL https://containerlab.dev/setup | sudo -E bash -s "all"
```

See: `https://containerlab.dev/install/#quick-setup`

Alternative options:

- macOS (Homebrew):

```bash
brew install containerlab
```

Verify:

```bash
containerlab version
docker version
```

## Bring up the lab

From the repository root:

```bash
cd container-lab-setup
containerlab deploy -t srl02.clab.yml
```

After deploy, containerlab will create `clab-srl02/` (runtime artifacts such as inventories and topology-data). Treat it as generated output.

### Inspect the lab

```bash
containerlab inspect -t srl02.clab.yml
```

You can also check containers:

```bash
docker ps --filter label=containerlab=srl02
```

## Access the nodes

### Option A: exec into SR Linux CLI

```bash
docker exec -it clab-srl02-srl1 sr_cli
docker exec -it clab-srl02-srl2 sr_cli
```

### Option B: SSH (management network)

Containerlab assigns management IPs on its mgmt bridge. In this lab:

- `srl1`: `172.20.20.2`
- `srl2`: `172.20.20.3`

Default admin credentials for Nokia SR Linux in this lab (as generated in `clab-srl02/ansible-inventory.yml`):

- username: `admin`
- password: `NokiaSrl1!`

Example:

```bash
ssh admin@172.20.20.2
ssh admin@172.20.20.3
```

## Validate connectivity

The startup configs configure IPv4/IPv6 on the inter-switch link:

- `srl1` `e1-1.0`: `192.168.0.0/31`, `2002::192.168.0.0/127`
- `srl2` `e1-1.0`: `192.168.0.1/31`, `2002::192.168.0.1/127`

From `sr_cli` on `srl1`, you can test reachability:

```text
ping 192.168.0.1
ping 2002::192.168.0.1
```

## Generated inventories

After `deploy`, containerlab writes inventories under `clab-srl02/`:

- `clab-srl02/ansible-inventory.yml` (Ansible)
- `clab-srl02/nornir-simple-inventory.yml` (Nornir)
- `clab-srl02/topology-data.json` (resolved topology, mgmt IPs, links)

## Tear down the lab

```bash
cd container-lab-setup
containerlab destroy -t srl02.clab.yml
```

If you want to remove generated runtime files too:

```bash
rm -rf clab-srl02
```
