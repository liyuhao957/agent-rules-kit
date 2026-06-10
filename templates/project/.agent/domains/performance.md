# Domain: Performance

## Use When

Changing hot paths, rendering, query/data loading, startup, memory, network, background work, bundle size, or repeated jobs.

## Verify Before Editing

- Current hot path and trigger frequency (record this project's known hot paths here during adapt-rules).
- Existing performance notes, tests, traces, metrics, or benchmarks.
- Whether the fix moves work, removes work, caches work, or only hides symptoms.
- Caching or concurrency additions have invalidation and lifecycle checked, not assumed.

## Done Means

The performance-sensitive path is no worse by inspection and, when practical, improved by measurement. No improvement claim without a metric, targeted reasoning, or before/after evidence.
