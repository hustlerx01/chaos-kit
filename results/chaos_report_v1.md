| Experiment | Resilience | Phase | req | err% | degraded% | p50 ms | p95 ms | hypothesis |
|---|---|---|---|---|---|---|---|---|
| inventory-sigkill | off | steady | 397 | 0.0 | 0.0 | 7.6 | 10.5 | PASS |
| inventory-sigkill | off | during | 397 | 100.0 | 0.0 | 6.7 | 12.3 | FAIL |
| inventory-sigkill | off | recovery | 397 | 0.0 | 0.0 | 7.7 | 12.8 | PASS |
| inventory-sigkill | on | steady | 397 | 0.0 | 0.0 | 7.5 | 12.3 | PASS |
| inventory-sigkill | on | during | 398 | 0.0 | 100.0 | 58.0 | 74.9 | PASS |
| inventory-sigkill | on | recovery | 397 | 0.0 | 0.0 | 7.6 | 13.0 | PASS |
| inventory-latency-500ms | off | steady | 398 | 0.0 | 0.0 | 7.6 | 13.0 | PASS |
| inventory-latency-500ms | off | during | 396 | 0.0 | 0.0 | 510.6 | 599.2 | FAIL |
| inventory-latency-500ms | off | recovery | 396 | 0.0 | 0.0 | 7.7 | 13.1 | PASS |
| inventory-latency-500ms | on | steady | 398 | 0.0 | 0.0 | 7.6 | 12.1 | PASS |
| inventory-latency-500ms | on | during | 397 | 0.0 | 100.0 | 658.5 | 661.6 | FAIL |
| inventory-latency-500ms | on | recovery | 397 | 0.0 | 0.0 | 8.1 | 14.1 | PASS |
| inventory-conn-drop-30pct | off | steady | 397 | 0.0 | 0.0 | 7.9 | 12.9 | PASS |
| inventory-conn-drop-30pct | off | during | 396 | 28.5 | 0.0 | 7.6 | 13.7 | FAIL |
| inventory-conn-drop-30pct | off | recovery | 397 | 0.0 | 0.0 | 7.7 | 13.0 | PASS |
| inventory-conn-drop-30pct | on | steady | 397 | 0.0 | 0.0 | 7.9 | 12.7 | PASS |
| inventory-conn-drop-30pct | on | during | 396 | 0.0 | 12.6 | 9.2 | 61.5 | PASS |
| inventory-conn-drop-30pct | on | recovery | 397 | 0.0 | 0.0 | 7.8 | 13.9 | PASS |
