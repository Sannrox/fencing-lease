import unittest

from scripts.tests.release import load

sbom = load("sbom")

WORKSPACE_ID = "fencing-lease 0.1.0 (path+file:///src/fencing-lease)"
METADATA = {
    "workspace_members": [WORKSPACE_ID],
    "packages": [
        {"id": "libc 0.2.0 (registry+https://github.com/rust-lang/crates.io-index)",
         "name": "libc", "version": "0.2.0", "license": "MIT OR Apache-2.0"},
        {"id": WORKSPACE_ID, "name": "fencing-lease", "version": "0.1.0", "license": "Apache-2.0"},
    ],
}


class BomFromMetadata(unittest.TestCase):
    def test_names_the_crate_with_the_fields_attest_sbom_requires(self):
        doc = sbom.bom_from_metadata(METADATA, "0.1.0")
        self.assertEqual(doc["bomFormat"], "CycloneDX")
        self.assertTrue(doc["specVersion"])
        self.assertTrue(doc["serialNumber"].startswith("urn:uuid:"))
        root = doc["metadata"]["component"]
        self.assertEqual((root["name"], root["version"], root["type"]), ("fencing-lease", "0.1.0", "library"))

    def test_lists_every_locked_package_with_its_license(self):
        components = sbom.bom_from_metadata(METADATA, "0.1.0")["components"]
        self.assertEqual([c["purl"] for c in components], ["pkg:cargo/fencing-lease@0.1.0", "pkg:cargo/libc@0.2.0"])
        crate, libc = components
        self.assertEqual(crate["licenses"], [{"license": {"id": "Apache-2.0"}}])
        self.assertEqual(crate["scope"], "required")
        self.assertEqual(libc["licenses"], [{"expression": "MIT OR Apache-2.0"}])

    def test_serial_number_is_stable_for_a_version(self):
        serial = lambda v: sbom.bom_from_metadata(METADATA, v)["serialNumber"]
        self.assertEqual(serial("0.1.0"), serial("0.1.0"))
        self.assertNotEqual(serial("0.1.0"), serial("0.2.0"))


if __name__ == "__main__":
    unittest.main()
