# Model Release Readiness Checklist

A one-page checklist to walk through before promoting any new model version to production. See `Notes/03-Model-Lifecycle-and-Rollout.mdx` for the reasoning behind each item.

## Before the rollout

- [ ] Model registered with lineage (training run, dataset version, eval metrics) - not just a file on disk
- [ ] Base-vs-tuned (or old-vs-new) benchmark table exists: quality delta, latency, cost per 1k requests
- [ ] Held-out eval set is versioned and was not used during training/tuning
- [ ] Rollback criteria written down and agreed, in numbers: max error rate, max p95 latency, min eval score, max refusal/tool-failure rate
- [ ] Rollback path is tested, not theoretical - confirm `helm rollback` (or equivalent) actually works before you need it
- [ ] Secrets and credentials audited - none present in prompts, logs, or the image itself
- [ ] PHI/PII redaction confirmed in place for any tracing/eval pipeline this model's traffic will flow through

## Rollout strategy

- [ ] Rollout strategy chosen deliberately (blue/green, canary, or champion-challenger) - not "just deploy it"
- [ ] If canary: starting traffic percentage and ramp schedule defined in advance
- [ ] If champion-challenger: minimum sample size before a promotion decision is made
- [ ] Dashboards/alerts wired to the rollback criteria above, not just general uptime

## After the rollout

- [ ] Rollback criteria monitored for an agreed observation window before calling it stable
- [ ] Audit log confirms who approved the promotion and when
- [ ] Registry updated to reflect the new `Production` stage and the previous version archived, not deleted
