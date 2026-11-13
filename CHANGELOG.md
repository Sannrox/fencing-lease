# Changelog

## [Unreleased]

## [0.1.2]

No library change from 0.1.0. First published release; `v0.1.1` failed at
SBOM attestation and has no GitHub Release. Consumers pinned to `v0.1.0`
can move to `v0.1.2` at will.

### Fixed

- The release SBOM carries a CycloneDX `serialNumber`, so SBOM attestation
  accepts it. The `v0.1.1` release failed on this and has no GitHub Release.

## [0.1.1]

No library change from 0.1.0. First release through the family release
workflow; consumers pinned to `v0.1.0` can move to `v0.1.1` at will.

### Added

- Family release workflow: a `v*` tag push dispatches `release.yml` from
  `main`, which verifies the signed tag against the allowed keys, runs the
  crate gates, packages the source archive, writes an SBOM, attests
  provenance, and publishes a GitHub Release with a signed family release
  manifest.

## [0.1.0]

- Named leases with acquire, renew, and release, and a monotonic fencing token
  per acquisition.
- `Fence` / `refuse_older`, `require_auto_promote` (two-node rule), and typed
  errors for fence loss, contention, and store unavailable.
- Backends: in-memory, local lock file (default), PostgreSQL (`postgres`),
  Kubernetes Lease (`kubernetes`).
- Moved from `Sannrox/agent-kit` (`crates/fencing-lease`) with its history.
  No API or behavior change. Declared minimum Rust is 1.88, which the locked
  dependencies already required.
- The `v0.1.0` tag was cut by an agent outside the release workflow and has
  no GitHub Release; consumers pin it as a plain signed tag.
