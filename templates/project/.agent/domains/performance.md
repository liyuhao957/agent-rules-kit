# Domain: Performance

## Use When

Changing hot paths, rendering, query/data loading, startup, memory, network, background work, bundle size, or repeated jobs.

## Verify Before Editing

- Current hot path and trigger frequency.
- Existing performance notes, tests, traces, metrics, or benchmarks.
- Whether the proposed fix moves work, removes work, caches work, or only hides symptoms.

## Do

- Prefer measurable evidence when available.
- Preserve correctness before optimizing.
- Keep changes local unless the performance issue crosses module boundaries.

## Do Not

- Add broad caching or concurrency without invalidation and lifecycle checks.
- Claim improvement without a metric, targeted reasoning, or before/after evidence.

## Done Means

The performance-sensitive path is no worse by inspection and, when practical, improved by measurement.

