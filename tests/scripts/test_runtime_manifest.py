# SPDX-License-Identifier: GPL-2.0-or-later
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from runtime_manifest import load_runtimes, native_file

class RuntimeManifestTests(unittest.TestCase):
    def load(self, entries):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "runtimes.props"
            path.write_text("<Project><ItemGroup>" + entries + "</ItemGroup></Project>")
            return load_runtimes(path)

    def test_runtime_metadata_drives_native_names(self):
        entry = self.load('<QualityRuntime Include="example-x64"><NativePrefix>prefix_</NativePrefix><NativeExtension>module</NativeExtension><Runner>example-runner</Runner></QualityRuntime>')[0]
        self.assertEqual(entry["os"], "example-runner")
        self.assertEqual(native_file(entry, "nfiq2"), "prefix_openphysical_nfiq2.module")

    def test_empty_or_duplicate_catalog_is_rejected(self):
        with self.assertRaises(ValueError): self.load("")
        with self.assertRaises(ValueError): self.load('<QualityRuntime Include="same"/><QualityRuntime Include="same"/>')

    def test_missing_metadata_and_path_components_are_rejected(self):
        with self.assertRaises(ValueError): self.load('<QualityRuntime Include="example-x64"/>')
        with self.assertRaises(ValueError): self.load('<QualityRuntime Include="../example"><NativePrefix>lib</NativePrefix><NativeExtension>so</NativeExtension><Runner>runner</Runner></QualityRuntime>')
