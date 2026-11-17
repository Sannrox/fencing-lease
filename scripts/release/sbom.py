#!/usr/bin/env python3
"""Write a CycloneDX 1.5 SBOM from `cargo metadata` (locked package, all features).

The source archive ships every optional backend, so the SBOM lists them too.
"""

from __future__ import annotations

import json
import re
import subprocess
import uuid
import sys
from pathlib import Path

COMPONENT = "fencing-lease"


def package_version(root: Path) -> str:
    text = (root / "Cargo.toml").read_text()
    match = re.search(
        r'(?ms)^\[package\][^\[]*?^version\s*=\s*"([^"]+)"',
        text,
    )
    if not match:
        raise SystemExit("Cargo.toml has no [package] version")
    return match.group(1)


def cargo_metadata(root: Path) -> dict:
    raw = subprocess.check_output(
        ["cargo", "metadata", "--locked", "--all-features", "--format-version", "1"],
        cwd=root,
        text=True,
    )
    return json.loads(raw)


def license_entries(license_text: str) -> list[dict]:
    text = license_text.strip()
    if re.fullmatch(r"[A-Za-z0-9.+-]+", text):
        return [{"license": {"id": text}}]
    return [{"expression": text}]


def bom_from_metadata(meta: dict, version: str) -> dict:
    workspace = set(meta.get("workspace_members") or [])
    packages = meta.get("packages") or []
    components = []
    for pkg in packages:
        pid = pkg.get("id")
        name = pkg.get("name")
        pkg_version = pkg.get("version")
        purl = f"pkg:cargo/{name}@{pkg_version}"
        component = {
            "type": "library",
            "bom-ref": purl,
            "name": name,
            "version": pkg_version,
            "purl": purl,
        }
        if pkg.get("license"):
            component["licenses"] = license_entries(pkg["license"])
        if pid in workspace:
            component["scope"] = "required"
        components.append(component)
    root_purl = f"pkg:generic/{COMPONENT}@{version}"
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        # actions/attest-sbom only recognizes CycloneDX with a serialNumber.
        # Derived from the root purl so a re-run for the same version is stable.
        "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, root_purl)}",
        "version": 1,
        "metadata": {
            "component": {
                "type": "library",
                "bom-ref": root_purl,
                "name": COMPONENT,
                "version": version,
                "purl": root_purl,
            }
        },
        "components": sorted(components, key=lambda item: item["bom-ref"]),
    }


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        raise SystemExit("usage: sbom.py OUT")
    root = Path(__file__).resolve().parents[2]
    bom = bom_from_metadata(cargo_metadata(root), package_version(root))
    out = Path(argv[0])
    out.write_text(json.dumps(bom, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv[1:])
