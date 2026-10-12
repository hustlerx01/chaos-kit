# Interview talking points: chaos-kit
1. **Hypothesis first.** "p95 ≤ 400 ms and errors ≤ 1% at the gateway" was written down before injecting anything. Chaos without a hypothesis is just breaking things.
2. **Retries can hurt.** My timeout + retry config made p95 worse (662 ms vs 603 ms naive). Retrying a slow dependency doubles latency and amplifies load. Retry only idempotent calls, only on errors that can succeed on retry, and with a budget.
3. **Fail fast + fallback.** Tuned mode (150 ms timeout, no retry on timeout, cache fallback) passed all 3 faults.
4. **Degraded isn't healthy.** 100% cache responses during the kill passed my hypothesis but could serve stale stock data. I'd add a degraded-ratio SLO and a staleness TTL.
5. **Validate the chaos tool.** Run 1 showed no effect because faults only hit new connections, and keep-alive pooling hid them. Always confirm the fault actually landed (a canary request with timing).
6. **Blast radius and rollback.** Each experiment rolls back automatically and verifies recovery. In prod: start in staging, then a small percentage of traffic, with an abort condition.
7. **Next.** A circuit breaker (stop paying timeouts during an outage), plus Chaos Mesh on K8s for pod-kill and network-delay at mesh level.
