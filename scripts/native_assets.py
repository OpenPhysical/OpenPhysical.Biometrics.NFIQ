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


def stage_runtime_licenses(source, destination):
    import os
    import shutil
    source, destination = Path(source), Path(destination)
    files = {}
    for folder in sorted(source.iterdir()):
        if not folder.is_dir() or folder.is_symlink():
            continue
        name = folder.name.lower()
        component = ("gcc" if "gcc" in name else "winpthreads" if "winpthread" in name
                     else "mingw-w64-libraries" if "mingw-w64-libraries" in name else None)
        if component is None:
            continue
        for directory, directories, names in os.walk(folder, followlinks=False):
            directories[:] = [d for d in directories if not (Path(directory) / d).is_symlink()]
            for name in names:
                path = Path(directory) / name
                if path.is_symlink() or not path.is_file():
                    continue
                key = (component, name)
                data = path.read_bytes()
                if key in files and files[key] != data:
                    raise ValueError(f"Conflicting runtime license: {component}/{name}")
                files[key] = data
    if not {"gcc", "winpthreads"} <= {component for component, name in files}:
        raise ValueError("Missing GCC or winpthreads runtime licenses.")
    if destination.exists():
        shutil.rmtree(destination)
    for (component, name), data in files.items():
        path = destination / component / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
