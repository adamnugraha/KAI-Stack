# Rail Reliability Lab — two demos, one synthetic application

**Purpose:** Train application and IT teams on system design, application modernization, SLIs/SLOs, fault isolation and SRE incident response. Entirely synthetic railway data. **Not production-grade, not a railway operational system.**

## Requirements

- Docker Engine with `docker compose` v2; about 4 vCPU and 8 GiB RAM recommended for smooth live demonstration.
- Local shell for running `curl`, Docker commands, and optionally `ssh`.
- On cloud/VPS hosts, Docker must be installed; only SSH from a trusted source should be publicly exposed. All demonstration ports are bound to `127.0.0.1` on the host.

## Quick start

```bash
cp .env.example .env
# Edit .env: choose strong, unique DEMO_ADMIN_KEY and GRAFANA_ADMIN_PASSWORD.
docker compose up -d --build
curl -s http://127.0.0.1:8080/legacy/search
curl -s http://127.0.0.1:8080/modern/search
```

Open locally:
- API (old): http://127.0.0.1:8080/legacy/search
- API (modern): http://127.0.0.1:8080/modern/search
- Grafana: http://127.0.0.1:3000/ (admin; password in `.env`), Dashboard → Demo → Rail Reliability Lab
- Prometheus: http://127.0.0.1:9090/alerts

If running on a VM, tunnel from the presentation laptop (replace host and username):

```bash
ssh -L 8080:127.0.0.1:8080 -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 -L 9080:127.0.0.1:9080 USER@HOST
```

**Use the following commands on the VM shell for fault injection and k6** (Grafana remains accessible through the tunnel). In these examples, `.env` is read by the shell only for the request; treat it as a secret.

```bash
set -a; . ./.env; set +a
# Start background traffic in one terminal
docker compose --profile load run --rm k6
# Another terminal: switch downstream into failure mode
curl -fsS -X POST -H "X-Demo-Key: $DEMO_ADMIN_KEY" http://127.0.0.1:9080/admin/mode/down
# Recover dependency
curl -fsS -X POST -H "X-Demo-Key: $DEMO_ADMIN_KEY" http://127.0.0.1:9080/admin/mode/healthy
```

## Demo 1 — modernization: dependency goes down

1. Show `legacy` → 1 replica → provider; `modern` → 2 replicas → provider with short timeout + explicitly stale read-only fallback.
2. Start k6 traffic. Dashboard shows healthy requests with outcomes `good`.
3. Set the provider to `slow` then `down`. Legacy may wait then emit 503; modern emits 200 + `outcome=degraded` + provenance of snapshot.
4. Important: HTTP 200 is not necessarily a **good journey**. The modernized app is HTTP-available but fails the high-quality freshness SLI during fallback. Do **not** claim 99.9% availability based on this lab's tiny observation window.
5. Recover provider to `healthy`. Explain timeout, failure isolation, fallback, stateless scaling, and end-user SLI.

## Demo 2 — SRE incident: an app replica dies

1. Return provider to `healthy`, then start k6 traffic again.
2. Stop one app replica: `docker compose stop modern-1`. NGINX retries / directs to the other replica. Inspect the gateway, application metrics, and remaining requests.
3. Stop the legacy app: `docker compose stop legacy`. Observe failure-rate difference.
4. Inspect alerts at http://127.0.0.1:9090/alerts and Grafana SLI charts. Discuss incident triage and business impact.
5. Recover with `docker compose start modern-1 legacy`; discuss automated replacement and rollback as future enhancements.

> Caution: Both modern replicas run on **one VM**. This lab is *process-level* redundancy only: VM, host, network, observability and provider failures may remain shared points of failure. Two app containers do NOT establish end-to-end 99.9% or 99.99% production availability. Persistent database, backup restore, regional and zone failure modes are not implemented.

## Service map

```text
client -> local SSH tunnel -> NGINX gateway
                                    |--> /legacy/search -> legacy app (1) -> provider
                                    `--> /modern/search -> modern app (2) -> provider
                                                                  `--> snapshot if dependency fails
legacy, modern-1, modern-2 -> Prometheus -> Grafana
k6 -> NGINX gateway
operator -> authenticated provider admin control (127.0.0.1:9080 only)
```

## Defined demo service objectives (illustrative, NOT proved)

- Request availability SLI: requests with HTTP status < 500 / eligible requests. This is an infrastructure-oriented SLI and is misleading alone when fallback data are stale.
- Good-journey SLI: `outcome=good` journey searches / all journey searches. Degraded results count as **not good**.
- Initial SLO example: >= 99.9% `good` journeys, measured over a rolling 28-day window *in a real production environment with user-meaningful eligibility and volumes*.
- Latency SLI: p95 search response time, including provider waits, with a user-approved threshold.
- Error-budget policy example: if the four-week budget is exhausted, prioritize reliability corrective actions and review release risk.
- RTO/RPO and database durability are separate requirements and are **not** demonstrated by this read-only lab.

## Notes on implementation

- The 'provider' is a mock, not KAI infrastructure. No external data are queried.
- The modern app uses a last-successful in-memory snapshot or bundled demo fallback. This illustrates graceful degradation **only for a clearly labeled read-only journey-info surface**. A real service needs freshness validation, cache provenance and safety requirements.
- Prometheus time series are local and ephemeral in this example; Grafana and Prometheus data are not persisted.
- Alerts are observable in Prometheus only. There is intentionally no public alert webhook/pager or automatic chaos injection.
- Some metrics may take ~1 minute to appear, since rate queries need observations.
- For a paid public-facing trial, add TLS, authentication, least privilege, resource quotas, version-pinned images, external monitoring, secrets handling and permanent observability.

## Cleanup

```bash
docker compose --profile load down --remove-orphans
```

Terminate paid cloud VMs, reserved IP addresses, disks, NAT gateways, load balancers and managed database resources separately after the workshop.

See `docs/slide-outline.md`, `docs/facilitator-runbook.md`, and `docs/cloud-deployment.md`.
