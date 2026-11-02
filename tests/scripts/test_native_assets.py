# SPDX-License-Identifier: GPL-2.0-or-later
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from native_assets import deduplicate_opencv, stage_runtime_licenses

class NativeAssetTests(unittest.TestCase):
    def test_materializes_loader_name_before_removing_alias_targets(self):
        for names in [("libopencv_core.so", "libopencv_core.so.410", "libopencv_core.so.4.10.0"),
                      ("libopencv_core.dylib", "libopencv_core.410.dylib", "libopencv_core.4.10.0.dylib")]:
            with self.subTest(names=names), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / names[2]).write_bytes(b"native library")
                (root / names[1]).symlink_to(names[2])
                (root / names[0]).symlink_to(names[1])
                deduplicate_opencv(root)
                self.assertEqual([p.name for p in root.iterdir()], [names[1]])
                self.assertFalse((root / names[1]).is_symlink())
                self.assertEqual((root / names[1]).read_bytes(), b"native library")

    def test_refuses_different_payloads(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "libopencv_core.so.410").write_bytes(b"one")
            (root / "libopencv_core.so").write_bytes(b"two")
            with self.assertRaises(ValueError): deduplicate_opencv(root)
            self.assertEqual(len(list(root.iterdir())), 2)

    def test_runtime_licenses_are_flat_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, target = root / "source", root / "target"
            for component in ["gcc", "libgcc", "libwinpthread", "winpthreads"]:
                path = source / component
                path.mkdir(parents=True)
                (path / "COPYING").write_bytes(b"license")
            (source / "gcc/back").symlink_to(source / "gcc", target_is_directory=True)
            stage_runtime_licenses(source, target)
            self.assertEqual(sorted(p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()),
                             ["gcc/COPYING", "winpthreads/COPYING"])
