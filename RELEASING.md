# Releasing

Consumers pin a signed tag: `tag = "vX.Y.Z"`. Any change to fencing
semantics (token ordering, error classification, promotion rules) is a
versioned change; in 0.x, a minor bump.

1. Land a pull request that sets `version` in `Cargo.toml` and moves the
   `CHANGELOG.md` Unreleased notes under the new version.
2. On that `main` commit, with CI green:

   ```sh
   git tag -s vX.Y.Z -m "fencing-lease vX.Y.Z"
   git push origin vX.Y.Z
   ```

The tag must equal `Cargo.toml`'s `version`. Tags are never moved or deleted.
