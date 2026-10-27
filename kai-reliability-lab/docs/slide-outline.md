# Deck blueprint — Engineering for 99.9%+ Availability

## Format
22–24 slides; no vendor sales pitch. Every concept is introduced as a question, a diagram, a live observation, or an operational decision. Use a synthetic KAI-adjacent passenger-information case study and label it fictional.

### Session 1 — Design & Modernize for Reliability (60 min)

| # | Min | Slide | Main content / speaker point |
|---|---:|---|---|
| 1 | 2 | Title & promise | System design + modernization + SRE are one lifecycle |
| 2 | 3 | What does 99.9% mean to a passenger? | Successful journey, not just server up |
| 3 | 4 | Reliability arithmetic | 30-day illustrative downtime: 99.9% ~43.2 min, 99.95% ~21.6 min, 99.99% ~4.32 min |
| 4 | 3 | Criticality tiers | Station info, booking, payments, operational systems have different obligations |
| 5 | 3 | Where failures come from | Bad releases, dependency loss, overload, VM/AZ loss, data and DNS failures |
| 6 | 5 | Rail Journey Service: user flow | Synthetic timetable lookup; avoid production passenger information |
| 7 | 5 | Before architecture | Client → single instance → synchronous provider; mark failure domains |
| 8 | 6 | After architecture | Load balancer, 2 replicas, timeouts, bounded fallbacks, telemetry |
| 9 | 4 | Modernization strategy | Start with boundaries / modular monolith, externalize configuration and state, strangler route, contract tests; not microservices first |
| 10 | 5 | Trade-off design review | What breaks if provider fails? What if host fails? Is stale data safe? |
| 11 | 15 | Demo 1 | Normal → slow → down → restore; compare baseline/modern; inspect end-user outcome |
| 12 | 5 | Lessons | Architecture shapes blast radius and recovery; 200 OK != reliable service |

### Session 2 — Operating with SRE (60 min)

| # | Min | Slide | Main content / speaker point |
|---|---:|---|---|
| 13 | 4 | SRE is an operating discipline | Reliability objectives, automation, safe change, incident learning |
| 14 | 5 | SLI / SLO / SLA | Define journey-quality SLI; SLO target; SLA contractual commitment |
| 15 | 4 | Error budget | 99.9% -> 0.1% failures; how to prioritize release vs stability |
| 16 | 4 | Golden signals | Latency, traffic, errors, saturation; symptom vs root cause |
| 17 | 4 | Telemetry map | API metrics (Prometheus) → charts (Grafana) → useful alerts |
| 18 | 4 | Alert on user harm | 5xx and degraded journey outcomes; avoid CPU-only alerting |
| 19 | 18 | Demo 2 | k6 traffic → replica down → compare paths → alerts → recovery |
| 20 | 5 | Incident response | Detect, declare, mitigate, communicate, restore, postmortem |
| 21 | 5 | 30/60/90-day KAI adoption roadmap | Inventory journeys; pilot SLI and runbook; progressive delivery and game days |
| 22 | 7 | Q&A and decision | Choose one bounded low-risk service and an SLO owner |

## Speaker techniques
- Open with a scenario: during a holiday surge, customers can open the app but not retrieve a trustworthy departure result. Is that 'available'?
- Ask the group to predict a failure before showing the demo, then reveal the metric.
- Show before/after diagrams with the same service contract, not different business logic.
- Talk about failure domains, change safety, and capacity before listing tools.
- Define 'good journey' explicitly: successful AND sufficiently fresh AND within an agreed latency threshold.
- Acknowledge that this sample labels *any* fallback degraded; production policy must define acceptable freshness and journey-specific safety constraints.
- Do NOT conflate passenger-facing apps with train control, signalling, safety, dispatching, or secure operational technology.

## Business-focused appendix slides
1. Risk tiering and critical user journeys: route search, ticket purchase, rebooking, check-in, disruption updates.
2. Fault tree / dependency map, single points of failure, isolation boundaries.
3. 30-day downtime budgets and request-based budgets are not the same mathematical measure.
4. Disaster recovery vs high availability: recovery time objective (RTO) and recovery point objective (RPO).
5. Deployment approaches: rolling, canary, blue/green, feature flags, automatic rollback.
6. DB resilience: transaction semantics, idempotency, concurrency, backups, and restore drills.
7. Technical debt prioritization by incident frequency, blast radius, impact, and expected error-budget gain.
8. Infrastructure mapping: one-host Docker demo vs multi-AZ cloud systems; managed != automatically meeting SLO.
