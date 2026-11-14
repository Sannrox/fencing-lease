# fencing-lease

**fencing-lease lets a standalone engine fail over to a standby without two
writers.**

At most one holder owns a named lease. A successor takes over after expiry or
release, and every takeover raises a fencing token. The engine refuses any
effect that carries an older token, so a paused holder that wakes up cannot
write after it lost the lease.

[![CI](https://img.shields.io/github/actions/workflow/status/Sannrox/fencing-lease/ci.yml?branch=main&label=ci)](https://github.com/Sannrox/fencing-lease/actions/workflows/ci.yml)
[![crates.io](https://img.shields.io/crates/v/fencing-lease)](https://crates.io/crates/fencing-lease)
[![docs.rs](https://img.shields.io/docsrs/fencing-lease)](https://docs.rs/fencing-lease)
[![License](https://img.shields.io/crates/l/fencing-lease)](https://github.com/Sannrox/fencing-lease/blob/main/LICENSE)

[Quickstart](#quickstart) · [When not to use](#when-not-to-use-fencing-lease) · [API docs](https://docs.rs/fencing-lease) · [Design](https://github.com/Sannrox/fencing-lease/blob/main/docs/decisions/0001-standalone-engine-ha.md) · [Changelog](https://github.com/Sannrox/fencing-lease/blob/main/CHANGELOG.md)

- **Fencing tokens.** A takeover raises the token, a renewal keeps it, and
  tokens never go backwards across restart.
- **Stale-writer refusal.** `Fence` and `refuse_older` reject an effect older
  than the highest admitted token.
- **Two-node rule.** `require_auto_promote` refuses automatic promotion for
  two members without a witness vote or an exclusive lock.
- **Typed errors.** Fence loss, contention, and an unavailable store stay
  distinct, so a lost fence is never retried as contention.
- **Pick your store.** File by default, PostgreSQL or Kubernetes behind a
  feature flag, memory for tests. No database required.

## When not to use fencing-lease

Choose another path when:

- You need consensus or replicated data. This crate decides who may write;
  your engine still owns its data durability.
- Your replicas are stateless. Run several and skip the lease.
- You already run a coordination service and want its leader election.
- You run two nodes and want automatic failover with no witness and no shared
  exclusive lock. Promotion stays manual there, by design.

## Quickstart

```sh
cargo add fencing-lease
```

Acquire a lease, admit its token at the engine, and watch a stale holder get
refused after takeover:

```rust
use std::time::Duration;

use fencing_lease::{Error, Fence, HolderId, LeaseName, LeaseStore, MemoryStore};

fn main() -> Result<(), Error> {
    let store = MemoryStore::new(); // FileStore::new(dir)? in production
    let name = LeaseName::new("orders-writer")?;
    let ttl = Duration::from_secs(10);

    // Node A takes the lease and writes with its token.
    let a = store.acquire(&name, &HolderId::new("node-a")?, ttl, 0)?;
    let mut fence = Fence::empty();
    fence.admit(a.token)?;

    // A pauses past its TTL. Node B takes over with a higher token.
    let b = store.acquire(&name, &HolderId::new("node-b")?, ttl, 20_000)?;
    fence.admit(b.token)?;

    // A wakes up and tries to write. The engine refuses it.
    assert!(matches!(fence.admit(a.token), Err(Error::FenceLost { .. })));
    Ok(())
}
```

In a real engine, pass `unix_now_ms()` as the clock, renew well inside the
TTL, and persist the highest admitted token next to the data it guards.

## Stores

| Store | Feature | Use |
| --- | --- | --- |
| `MemoryStore` | default | Tests |
| `FileStore` | default, unix | Standalone; a shared mount gives an exclusive lock across members |
| `PostgresStore` | `postgres` | Row-locked lease in an existing database |
| `KubernetesStore` | `kubernetes` | `coordination.k8s.io` Lease objects |

Default features pull in neither PostgreSQL nor Kubernetes.

## Development

```sh
cargo fmt --all -- --check
cargo test --locked
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked --features postgres,kubernetes
cargo clippy --locked --all-targets --features postgres,kubernetes -- -D warnings
```

PostgreSQL backend tests run only when `FENCING_LEASE_POSTGRES_URL` is set.
Release-path checks: `bash scripts/validate-release.sh`.
Releases: [RELEASING.md](https://github.com/Sannrox/fencing-lease/blob/main/RELEASING.md).

## License

Apache-2.0
