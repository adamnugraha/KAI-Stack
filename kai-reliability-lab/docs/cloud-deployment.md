# Portable deployment guide: VPS, AWS, GCP

## Architecture strategy
**Level 1 (the live teaching lab):** ONE Linux host with Docker Compose. Identical code and instructions whether it is a pre-existing VPS, EC2 VM, or Google Compute Engine VM. Demo process-level redundancy and bounded fallback, not host/zone-level HA.

**Level 2 (discussion of what production needs):** independent failure domains for replicas, zone-aware load balancing, durable state, backups/restore tests, independent monitoring, CI/CD, secrets and cost guardrails. Managed primitives differ by platform; don't imply you can `docker compose up` directly into ECS or Cloud Run without adapting services, ingress, telemetry and storage.

## Choose one primary teaching environment
| Host | Suggested for | Trade-offs |
|---|---|---|
| Existing VPS | **Live demo primary** if stable and reachable | Lowest setup friction, no multi-AZ, host and access-path failures remain |
| AWS EC2 VM | Dry-run copy and AWS relevance | Same Docker Compose, billable compute, disk, IP/data costs |
| GCP Compute Engine VM | Dry-run copy and GCP relevance | Same Docker Compose, billable compute, disk, IP/data costs |

For a 2-hour session, run the demo from **one** environment and show a service-mapping slide for the other providers. Do not try to operate all three simultaneously unless each has already been tested and you specifically need a portability comparison.

## Shared host setup (Ubuntu 24.04 LTS)
1. Provision a test host with ~4 vCPU, 8GiB memory, 20GiB+ disk; adapt to performance and budget. This is an *engineering suggestion*, not a guarantee.
2. Keep all Docker-published demo ports bound to 127.0.0.1 (already set in `compose.yaml`). Expose only SSH (prefer trusted-IP allowlist, VPN, or a managed session service). Don't expose Grafana/Prometheus/provider-admin publicly.
3. Install Docker Engine and the Compose v2 plugin using Docker's **current official Ubuntu apt repository** instructions: https://docs.docker.com/engine/install/ubuntu/ . Avoid convenience scripts for a reusable internet-facing host; ensure access and permissions are controlled.
4. Transfer the unzipped lab or check out the repository, then create `.env` from `.env.example`. Keep `.env` private and out of Git.
5. Run `docker compose up -d --build` and `docker compose ps`; check URLs from the host. Tunnel ports via SSH from the presentation laptop using the command in README.
6. Load test with the included k6 tool, fault-inject provider only via localhost authenticated endpoint, and recover before the audience leaves.
7. Tear down cloud resources at the end. Billing budgets are alerts, not a hard cap in general.

## Existing VPS
- Verify kernel, CPU, available memory and disk space; don't risk an existing business-critical service.
- Ubuntu 24.04 LTS preferred for the repeatable instructions.
- Firewall: trusted-source SSH only; NO public ingress for 3000, 8080, 9080 or 9090.
- Use existing VPN/SSH access; demo traffic stays within the host.
- If latency from the venue is uncertain, prepare local laptop clone and screenshots.

## AWS test host: EC2
1. Select a region near your audience/venue, subject to organizational policy; isolate the lab in a test account/project.
2. EC2 → Launch instance: Ubuntu 24.04 LTS, an instance class with approximately 4 vCPU / 8GiB, ~20GiB disk, a suitable VPC subnet with outbound access for image pulls.
3. Security group inbound: SSH TCP/22 **only from the speaker's current public IP** or use AWS Systems Manager Session Manager instead. No other inbound demo ports.
4. Access the host over SSH, follow shared Docker setup, copy this lab and run `docker compose up -d --build`.
5. If using SSH tunnel, Grafana appears at http://127.0.0.1:3000 on your presentation laptop; the endpoint is NOT exposed to the internet.
6. Set AWS Budgets alerts BEFORE resources are created; review EC2, storage, public IPv4 charges, egress and any NAT/balancer/managed DB that you add. Terminate/delete resources, volumes and unused reserved resources afterward.

AWS managed HA **architecture discussion** (not implemented in the starter lab): Route 53 / edge controls → public Application Load Balancer across 2 AZs → ECS Fargate with minimum 2 tasks distributed across AZs → RDS Multi-AZ for transactional data → CloudWatch and/or managed Prometheus/Grafana → safe deployment with health gates and rollback. Multi-AZ RDS reduces database failure risk; a single-AZ database would still be a critical dependency. See https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-load-balancing.html and https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html .

## Google Cloud test host: Compute Engine
1. Isolate the lab in a Google Cloud project and create a billing budget/alert.
2. Compute Engine → Create instance: Ubuntu 24.04 LTS, around 4 vCPU / 8GiB, 20GiB+ disk, a region and zone appropriate for the test.
3. Avoid selecting an allow-all HTTP ingress. Use the Google Cloud Console SSH or restrict public TCP/22 to your trusted IP; no firewall rules for 3000/8080/9080/9090.
4. Connect with SSH, install official Docker Engine + Compose, transfer project and run `docker compose up -d --build`.
5. For remote access, use `gcloud compute ssh INSTANCE --zone=ZONE -- -L 8080:127.0.0.1:8080 -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 -L 9080:127.0.0.1:9080` when the CLI and identity are configured, or an ordinary SSH tunnel.
6. Delete the VM and any unattached disks/addresses after the workshop; watch cost and egress.

GCP managed HA **architecture discussion** (not implemented in the starter lab): Cloud Load Balancing/Cloud Armor as applicable → Cloud Run service with healthy revisions and suitable scaling settings (or zonally distributed GKE) → Cloud SQL configured for **regional HA** → Cloud Monitoring and managed Prometheus/Cloud Trace → gradual rollout and fast rollback. Cloud Run deployment from a container and scaling are documented at https://docs.cloud.google.com/run/docs/deploying; Cloud SQL HA at https://docs.cloud.google.com/sql/docs/availability . Do not imply that one Cloud Run service by itself ensures the end-user's entire journey meets a given availability target.

## Comparison — native destination mapping
| Capability | One-host lab | AWS production direction | GCP production direction |
|---|---|---|---|
| Entry / traffic control | NGINX | ALB / WAF | Cloud LB / Cloud Armor |
| Run application | Docker containers | ECS Fargate (2+ AZs) | Cloud Run or GKE |
| Durable relational data | Not implemented | RDS Multi-AZ | Cloud SQL regional HA |
| Metrics/dashboard | Prometheus + Grafana | CloudWatch / AMP / AMG | Cloud Monitoring / Managed Prometheus |
| Synthetic load | k6 in Compose | k6 on isolated test runner | k6 on isolated test runner |
| Fault injection | provider admin + stop container | controlled task/zone/dependency scenario | controlled instance/revision/dependency scenario |
| Recovery | manual restart / NGINX retry | service auto-replace, deployment rollback | platform autoscaling/revisions, rollback |

## Security and budget guardrails
- Isolate demo infra from corporate networks and train operational technology.
- Use fake journey fixtures only; no employee, passenger, payment or live train data.
- Never target real KAI or partner APIs with k6 or chaos tests.
- Rotate demo passwords, restrict SSH, keep dashboards/admin on loopback, turn off lab when idle.
- Budget alert does NOT physically stop spend; resource lifecycle and manual/automated cleanup are necessary.
- On managed deployments, load balancers, NAT gateways, databases, logs and cross-zone/region traffic can cost more than the app containers.
