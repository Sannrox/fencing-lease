# ADR 0001: Standalone engine HA: fenced leases and the two-node rule

- Status: Accepted
- Date: 2026-10-30
- Issue: [#1](https://github.com/Sannrox/agent-kit/issues/1)

## Context

Several standalone engines need single-writer failover. Each was heading for
its own lease store and fencing rules. Fencing is where subtle bugs sit
(clock skew, a paused holder that wakes, treating fence loss as contention),
and separate implementations will drift. The engines cannot depend on a
governance-plane lease service, and a standalone build cannot require a
database.

This decision is the shared pattern. The library that implements it lives in
this repository as the `fencing-lease` crate.

## Decision

### 1. Vocabulary

| Term | Meaning |
| --- | --- |
| Stateless replica | A process that can die and be replaced; it holds no unique durable state. |
| Active/passive with a lease | At most one holder may write. The holder renews a named lease. A successor takes the lease after expiry or release. |
| State replication | Engine data is copied by the engine, not by the lock store. |
| Durable resume | Restart or restore against engine-owned durable state. Recovery is not availability. |

A single shared database moves the single point of failure; it does not
remove it. A profile only removes that point when the database itself is
replicated with measured failover.

### 2. Two-node rule

With two members there is no majority. Automatic promotion requires a third
witness vote **or** a storage-level exclusive lock (PostgreSQL row lock,
Kubernetes Lease, or a lock file on storage every member mounts). Otherwise
promotion is manual, through an explicit operator action.

`fencing_lease::require_auto_promote` is that gate. The library does not run
a witness protocol; the caller reports whether a witness vote is in hand.
Three or more members without an exclusive lock or a witness still refuse
automatic promotion: this library is not consensus.

### 3. Lock store versus engine data

The lock store decides **who may write**. Engine data durability stays in the
engine (write-ahead logs, snapshots, checkpoints, store-and-forward buffers).
A lock-store outage must not be the engine's durability outage.

### 4. Drill evidence

A failover drill records, for each of: kill the holder, partition the holder,
pause the holder past the lease:

| Field | What it measures |
| --- | --- |
| Interruption window | Time from loss until a successor holds the lease |
| Acknowledged-loss bound | The engine's bound on data it had acknowledged and then lost |
| Remaining single points of failure | What still cannot fail without losing the write path |

### 5. Library location

The library is the `fencing-lease` crate in its own repository,
`Sannrox/fencing-lease`. Engines depend on it with a Cargo git dependency
pinned to a signed `v*` tag. Default features are the in-memory store and
the local lock file. PostgreSQL and Kubernetes Lease backends sit behind
features. Engines do not depend on each other.

The crate first lived beside this ADR in `Sannrox/agent-kit`. It moved out
(Sannrox/agent-kit#44) because its version was tied to the skill kit's
release cadence and consumers pinned a commit in a skills repository instead
of a library version.

### 6. Library contract

- Acquire, renew, and release a named lease.
- A monotonically increasing fencing token per acquisition. A renewal keeps
  the token. A takeover raises it. Tokens do not go backwards across restart.
- `Fence` / `refuse_older` refuse an effect whose token is older than the
  highest admitted token.
- Typed errors keep **fence loss**, **contention**, and **store
  unavailable** distinct.
- Backends: in-memory (tests), local lock file (default standalone),
  PostgreSQL (feature), Kubernetes Lease (feature).
- A standalone build without the PostgreSQL and Kubernetes features still
  runs on one node with the lock file.

## Consequences

- Consumer issues adopt the crate; they do not invent a second lease store.
- In-store fencing that a control plane already does inside its own
  transactions stays there. This crate does not replace it.
- Default builds stay free of PostgreSQL and Kubernetes dependencies.

## Rejected alternatives

| Option | Why rejected |
| --- | --- |
| Keep the crate in the shared skill kit | Ties library versions to skill releases; consumers pin a commit of an unrelated repository. Superseded by Sannrox/agent-kit#44. |
| Publish the crate from an engine repository | Other engines would depend on a peer engine. |
| Multi-writer consensus | Out of scope. Crash-safe storage, idempotent APIs, and fencing suffice. |
| Put engine data in the lock store | Couples durability to the lock; a lock outage becomes data loss. |
| Lease timing without a fencing token | Unsafe under clock skew and a paused holder that resumes. |
| Treat fence loss as contention | Callers retry a fenced generation as if the holder were merely busy. |
| Automatic promotion of two nodes without a witness or exclusive lock | Split-brain. |
