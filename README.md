# fencing-lease

Named fencing leases for standalone engines: at most one holder writes, a
successor takes over after expiry or release, and a fencing token lets the
engine refuse effects from a stale holder.

Pattern and contract: [ADR 0001](docs/decisions/0001-standalone-engine-ha.md).

```toml
fencing-lease = { git = "https://github.com/Sannrox/fencing-lease", tag = "v0.1.0" }
```

- Acquire, renew, and release a named lease. A takeover raises the fencing
  token; a renewal keeps it; tokens never go backwards across restart.
- `Fence` / `refuse_older` refuse an effect older than the highest admitted
  token.
- `require_auto_promote` gates automatic promotion (the two-node rule).
- Typed errors keep fence loss, contention, and store unavailable distinct.

Backends: `MemoryStore` (tests), `FileStore` (default standalone, unix),
`PostgresStore` (feature `postgres`), `KubernetesStore` (feature
`kubernetes`). Default features pull in neither PostgreSQL nor Kubernetes.

## Development

```sh
cargo fmt --all -- --check
cargo test --locked
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked --features postgres,kubernetes
cargo clippy --locked --all-targets --features postgres,kubernetes -- -D warnings
```

PostgreSQL backend tests run only when `FENCING_LEASE_POSTGRES_URL` is set.
Releases: [RELEASING.md](RELEASING.md).

## License

Apache-2.0
