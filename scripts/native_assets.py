# SPDX-License-Identifier: GPL-2.0-or-later
"""Normalize installed native assets without changing their loader identities."""
import re
from pathlib import Path


def deduplicate_opencv(stage):
    stage = Path(stage)
    groups = {}
    for path in stage.glob("libopencv_*"):
        match = re.fullmatch(r"(libopencv_[a-z0-9_]+)(?:\.so(?:\.[0-9.]+)?|(?:\.[0-9.]+)?\.dylib)", path.name)
        if match:
            groups.setdefault(match[1], []).append(path)
    for component, paths in groups.items():
        canonical = [p for p in paths if re.fullmatch(re.escape(component) + r"(?:\.so\.\d+|\.\d+\.dylib)", p.name)]
        if len(canonical) != 1:
            raise ValueError(f"Expected one OpenCV ABI filename: {component}")
        keep = canonical[0]
        data = keep.read_bytes()
        mode = keep.stat().st_mode
        if any(p.read_bytes() != data for p in paths):
            raise ValueError(f"OpenCV aliases differ: {component}")
        # Materialize the ABI name before deleting the target of its symlink.
        if keep.is_symlink():
            keep.unlink()
            keep.write_bytes(data)
            keep.chmod(mode)
        for path in paths:
            if path != keep:
                path.unlink()
