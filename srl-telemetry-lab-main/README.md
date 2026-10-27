# Nokia SR Linux Streaming Telemetry Lab


SR Linux has first-class Streaming Telemetry support thanks to [100% YANG coverage](https://learn.srlinux.dev/yang/) of state and config data. The holistic coverage enables SR Linux users to stream **any** data off of the NOS with on-change, sample, or target-defined support. A discrepancy in visibility across APIs is not about SR Linux.

This lab represents a small Clos fabric with [Nokia SR Linux](https://learn.srlinux.dev/) switches running as containers. The lab topology consists of a Clos topology, plus a Streaming Telemetry stack comprised of [gnmic](https://gnmic.openconfig.net), prometheus and grafana applications.

---

![pic1](https://gitlab.com/rdodin/pics/-/wikis/uploads/0784c31d48ec18fd24111ad8d73478b0/image.png)

In addition to the telemetry stack, the lab also includes a modern logging stack comprised of [Grafana Alloy](https://grafana.com/docs/alloy/latest/) and [loki](https://grafana.com/oss/loki/).

Goals of this lab:

1. Demonstrate how a telemetry stack can be incorporated into the containerlab topology file.
2. Explain SR Linux holistic telemetry support.
3. Provide practical configuration examples for the gnmic collector to subscribe to fabric nodes and export metrics to Prometheus TSDB.
4. Introduce advanced Grafana dashboarding with [FlowPlugin](https://grafana.com/grafana/plugins/andrewbmchugh-flow-panel/) plugin rendering port speeds and statuses.
5. Give a sneak peek of the modern logging telemetry stack with Loki and Promtail to consume Syslog data from SR Linux nodes.

## Deploying the lab

The lab is deployed with the [containerlab](https://containerlab.dev) project, where [`st.clab.yml`](st.clab.yml) file declaratively describes the lab topology.

```bash
# change into the cloned directory
# and execute
containerlab deploy --reconfigure
```

To remove the lab:

```bash
containerlab destroy --cleanup
```

## Accessing the network elements

Once the lab has been deployed, the different SR Linux nodes can be accessed via SSH through their management IP address, given in the summary displayed after the execution of the deploy command. It is also possible to reach those nodes directly via their hostname, defined in the topology file. Linux clients cannot be reached via SSH, as it is not enabled, but it is possible to connect to them with a docker exec command.

```bash
# reach a SR Linux leaf or a spine via SSH
ssh admin@leaf1
ssh admin@spine1

# reach a Linux client via Docker
docker exec -it client1 bash
```

## Fabric configuration

The DC fabric used in this lab consists of three leaves and two spines interconnected as shown in the diagram.

![pic](https://gitlab.com/rdodin/pics/-/wikis/uploads/14c768a04fc30e09b0bf5cf0b57b5b63/image.png)

Leaves and spines use Nokia SR Linux IXR-D2 and IXR-D3L chassis respectively. Each network element of this topology is equipped with a [startup configuration file](configs/fabric/) that is applied at the node's startup.

Once booted, network nodes will come up with interfaces, underlay protocols and overlay service configured. The fabric is running Layer 2 EVPN service between the leaves.

### Verifying the underlay and overlay status

The underlay network runs eBGP, while iBGP is used for the overlay network. The Layer 2 EVPN service is configured as explained in this comprehensive tutorial: [L2EVPN on Nokia SR Linux](https://learn.srlinux.dev/tutorials/l2evpn/intro/).

By connecting via SSH to one of the leaves, we can verify the status of those BGP sessions.

```
A:leaf1# show network-instance default protocols bgp neighbor
------------------------------------------------------------------------------------------------------------------
BGP neighbor summary for network-instance "default"
Flags: S static, D dynamic, L discovered by LLDP, B BFD enabled, - disabled, * slow

+-----------+---------------+---------------+-------+----------+-------------+--------------+--------------+---------------+
| Net-Inst  |     Peer      |     Group     | Flags | Peer-AS  |   State     |    Uptime    |   AFI/SAFI   | Rx/Active/Tx] |
+===========+===============+===============+=======+==========+=============+==============+==============+===============+
| default   | 10.0.2.1      | iBGP-overlay  | S     | 100      | established | 0d:0h:0m:27s | evpn         | [4/4/2]       |
| default   | 10.0.2.2      | iBGP-overlay  | S     | 100      | established | 0d:0h:0m:28s | evpn         | [4/0/2]       |
| default   | 192.168.11.1  | eBGP          | S     | 201      | established | 0d:0h:0m:34s | ipv4-unicast | [3/3/2]       |
| default   | 192.168.12.1  | eBGP          | S     | 202      | established | 0d:0h:0m:33s | ipv4-unicast | [3/3/4]       |
+-----------+---------------+---------------+-------+----------+-------------+--------------+--------------+---------------+
```

## Telemetry stack

As the lab name suggests, telemetry is at its core. The following telemetry stack is used in this lab:

| Role                | Software                              |
| ------------------- | ------------------------------------- |
| Telemetry collector | [gnmic](https://gnmic.openconfig.net) |
| Time-Series DB      | [prometheus](https://prometheus.io)   |
| Visualization       | [grafana](https://grafana.com)        |

### gnmic

[gnmic](https://gnmic.openconfig.net) is an Openconfig project that allows to subscribe to streaming telemetry data from network devices and export it to a variety of destinations. In this lab, gnmic is used to subscribe to the telemetry data from the fabric nodes and export it to the prometheus time-series database.

The gnmic configuration file - [configs/gnmic/gnmic-config.yml](./configs/gnmic/gnmic-config.yml) - is applied to the gnmic container at the startup and instructs it to subscribe to the telemetry data and export it to the prometheus time-series database.

### Prometheus

[Prometheus](https://prometheus.io) is a popular open-source time-series database. It is used in this lab to store the telemetry data exported by gnmic. The prometheus configuration file - [configs/prometheus/prometheus.yml](configs/prometheus/prometheus.yml) - has a minimal configuration and instructs prometheus to scrape the data from the gnmic collector with a 5s interval.

### Grafana

Grafana is another key component of this lab as it provides the visualisation for the collected telemetry data. Lab's topology file includes grafana node and configuration parameters such as dashboards, datasources and required plugins.

Grafana dashboard provided by this repository provides multiple views on the collected real-time data. Powered by [flow plugin](https://grafana.com/grafana/plugins/andrewbmchugh-flow-panel/) it overlays telemetry sourced data over graphics such as topology and front panel views:

![pic3](https://gitlab.com/rdodin/pics/-/wikis/uploads/919092da83782779b960eeb4b893fb4a/image.png)

Using the flow plugin and real telemetry data users can create interactive topology maps (aka weathermap) with a visual indication of link rate/utilization.

![pic2](https://gitlab.com/rdodin/pics/-/wikis/uploads/12f154dafca1270f7a1628c1ed3ab77a/image.png)

The panels for the flow plugin has been autocreated by the [clab-io-draw](https://github.com/srl-labs/clab-io-draw) tool

### netops-autopilot alert database UI

The `sqlite-web` node runs [coleifer/sqlite-web](https://hub.docker.com/r/coleifer/sqlite-web), binding the repository's [`../var/`](../var) directory so that `../var/netops-autopilot.db` (the default `NETOPS_DATABASE_PATH`) can be browsed and queried from a web UI whenever the lab is deployed. If `NETOPS_DATABASE_PATH` is pointed at a different file, update the `SQLITE_DATABASE` env value for the `sqlite-web` node in [st.clab.yml](st.clab.yml) to match.

The topology drawing uses custom icons stored in [`.clab-icons/`](.clab-icons/). Each node's annotation in [st.clab.yml.annotations.json](st.clab.yml.annotations.json) sets `icon` to the icon file's basename, so `sqlite-web` uses `.clab-icons/sqlite-web.svg`.

### Access details

Using containerlab's ability to expose ports of the containers to the host, the following services are available on the host machine:

* Grafana: <http://localhost:3000>. Anonymous access is enabled; no credentials are required. If you want to act as an admin, use `admin/admin` credentials.
* Prometheus: <http://localhost:9090/graph>
* netops-autopilot alert database (sqlite-web): <http://localhost:8080>

### Alerting

Grafana alert rules are provisioned from disk under [configs/grafana/alerting/](configs/grafana/alerting/), mounted into the `grafana` container at `/etc/grafana/provisioning/alerting`. Rules defined there are loaded automatically on every container start/redeploy (including `containerlab deploy --reconfigure`), so they don't need to be recreated manually through the UI.

The lab currently ships one rule, [interface-down-rules.yml](configs/grafana/alerting/interface-down-rules.yml):

* **Leaf1 Interface Down** (folder `NetOps Alerts`, group `interface-health`) queries `interface_oper_state{source="leaf1", interface_name=~"e1-1|e1-49|e1-50"}` from Prometheus and fires when any of those interfaces reports `0` (down) for at least 10 seconds.
* The query is scoped to only the interfaces actually cabled for leaf1 in [st.clab.yml](st.clab.yml) (`e1-1` to `client1`, `e1-49` to `spine1`, `e1-50` to `spine2`). Leaf1's remaining ethernet ports are unconnected and legitimately report `oper-state: down`, so they are excluded to avoid alert noise.
* View it in Grafana under **Alerting → Alert rules → NetOps Alerts → Leaf1 Interface Down**.
* To test it, admin-disable one of the three cabled interfaces on leaf1 (e.g. `ethernet-1/49`) via its SR Linux CLI and watch the rule transition from `Normal` to `Pending` to `Alerting` in the Grafana Alerting page.

The [Prometheus datasource](configs/grafana/datasource.yml) is provisioned with a fixed `uid` (`PBFA97CFB590B2093`) so that alert rules referencing it remain valid across redeploys.

#### Forwarding alerts to netops-autopilot

[configs/grafana/alerting/contact-points.yml](configs/grafana/alerting/contact-points.yml) and
[configs/grafana/alerting/notification-policies.yml](configs/grafana/alerting/notification-policies.yml)
route firing/resolved alerts from a Grafana `webhook` contact point to the
netops-autopilot FastAPI server's `POST /v1/webhooks/grafana` endpoint, which
translates Grafana's native alert payload into the `AlertInput` schema and
ingests it the same way as `POST /v1/alerts`.

To use it end to end:

1. Start the API on the host so the `grafana` container can reach it: `uvicorn netops_autopilot.api:app --host 0.0.0.0 --port 8000`.
2. Confirm the contact point's webhook URL matches your `st` docker network gateway: `docker network inspect st --format '{{(index .IPAM.Config 0).Gateway}}'`. Update `configs/grafana/alerting/contact-points.yml` if it differs from `172.80.80.1`, then `containerlab deploy --reconfigure`.
3. Admin-disable `ethernet-1/49` on leaf1 (see above). Once the rule reaches `Alerting`, Grafana POSTs to the contact point and the alert appears via `GET /v1/alerts` (and `GET /v1/metrics`) on the API.
4. Re-enable the interface (`admin-state enable` + `commit now`) to see the matching `resolved` alert ingested as a separate event.

## Logging stack

The logging stack leverages the Alloy->Loki pipeline, where Alloy receives syslog messages, transforms labels, and ships logs to Loki, a log aggregation system.

The logging infrastructure logs every message from SR Linux that is above Info level. This includes all the BGP messages, all the system messages, all the interface state changes, etc. The dashboard provides a view on the collected logs and allows filtering on a per-application level.

## Traffic generation

When the lab is started, there is not traffic running between the nodes as the clients are sending any data. To run traffic between the nodes, leverage `traffic.sh` control script.

To start the traffic:

* `bash traffic.sh start all` - start traffic between all nodes
* `bash traffic.sh start 1-2` - start traffic between client1 and client2
* `bash traffic.sh start 1-3` - start traffic between client1 and client3

To stop the traffic:

* `bash traffic.sh stop all` - stop traffic generation between all nodes
* `bash traffic.sh stop 1-2` - stop traffic generation between client1 and client2
* `bash traffic.sh stop 1-3` - stop traffic generation between client1 and client3

As a result, the traffic will be generated between the clients and the traffic rate will be reflected on the grafana dashboard.

<https://github.com/srl-labs/srl-telemetry-lab/assets/5679861/158914fc-9100-416b-8b0f-cde932895cec>
