# Facilitator runbook

## Prepare 3–7 days before
1. Put the lab on one host only (VPS OR cloud VM) and test from presentation laptop through SSH forwarding.
2. Record short fallback video clips or screenshots of the normal, slow, down and replica-kill phases in case venue internet is unstable. The recording is a contingency, not claimed real-time evidence.
3. Verify the user journey and its **good** criterion. For the live demo, all stale results are explicitly degraded and excluded from good-journey counts.
4. Set Grafana dashboard refresh to 5 sec and time range to 15 minutes. Warm traffic first; rate queries need enough samples.
5. Confirm dashboard scale, font readability and terminal zoom at projector resolution.
6. Reserve time and budget for 1–2 rehearsals, not a production HA proof.

## Rehearsal command sequence
```bash
cp .env.example .env
# Replace secrets.
docker compose up -d --build
set -a; . ./.env; set +a
curl -fsS -X POST -H "X-Demo-Key: $DEMO_ADMIN_KEY" http://127.0.0.1:9080/admin/mode/healthy
curl -si 'http://127.0.0.1:8080/legacy/search'
curl -si 'http://127.0.0.1:8080/modern/search'
# In separate terminal: generate both legacy and modern search traffic.
docker compose --profile load run --rm k6
```

## Demo 1 — about 15–20 min including audience discussion
- 0–3 min: ask whether a 200 status always meets journey expectations; show baseline and after diagram.
- 3–5 min: healthy traffic, p95, no errors and good journeys.
- 5–9 min: `POST /admin/mode/slow`. Baseline gets slow, modern responds quickly using marked stale snapshot; compare HTTP vs good-journey SLI.
- 9–13 min: `POST /admin/mode/down`. Baseline 503, modern 200 but degraded. Review reliability trade-offs.
- 13–15 min: `POST /admin/mode/healthy`; highlight freshness policy and business correctness.

## Demo 2 — about 18–20 min including audience discussion
- 0–3 min: healthy state and traffic; metrics live.
- 3–6 min: `docker compose stop modern-1`. NGINX forwards requests to modern-2. Count any transient errors; do not promise zero.
- 6–10 min: `docker compose stop legacy`. Single instance path fails. Compare direct observable outcomes.
- 10–14 min: view alert expressions and alerts in Prometheus; discuss that alerts need symptoms and owner/action.
- 14–16 min: `docker compose start modern-1 legacy`; retest and confirm recovery.
- 16–20 min: identify shared single-host SPOF, unimplemented database, RTO/RPO and multi-zone HA.

## One-minute rollback / reset
```bash
set -a; . ./.env; set +a
curl -fsS -X POST -H "X-Demo-Key: $DEMO_ADMIN_KEY" http://127.0.0.1:9080/admin/mode/healthy
docker compose start legacy modern-1 modern-2
```

## Questions to pose to KAI technical teams
- Which 2–3 passenger journeys matter most during peak travel dates?
- Is the failure SLI evaluated at browser, mobile client, gateway, app or database?
- What freshness limits should apply to timetable vs occupancy/seat inventory?
- Can a release be rolled back in 5 minutes, and who authorizes it?
- Which dependencies lie outside the application's team's control?
- Is incident review blameless and tied to measurable corrective action?

## Risks and limitations
- One VPS or VM hosts both modern replicas; host loss remains a full outage.
- Simulated provider and snapshot are synthetic; testing does not demonstrate real KAI availability.
- Metrics are useful for live teaching, not formal attainment of any 99.x SLO.
- No user authentication is built into the read-only lab API, so localhost binding and SSH tunneling are deliberate.
- Do not turn load-testing traffic towards third-party, shared, or KAI production endpoints.
