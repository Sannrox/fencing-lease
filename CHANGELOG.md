# Changelog

## Unreleased

## 0.1.0

- Named leases with acquire, renew, and release, and a monotonic fencing token
  per acquisition.
- `Fence` / `refuse_older`, `require_auto_promote` (two-node rule), and typed
  errors for fence loss, contention, and store unavailable.
- Backends: in-memory, local lock file (default), PostgreSQL (`postgres`),
  Kubernetes Lease (`kubernetes`).
- Moved from `Sannrox/agent-kit` (`crates/fencing-lease`) with its history.
  No API or behavior change.
