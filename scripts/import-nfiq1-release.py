#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Decode the official NBIS release NFIQ vectors with original NBIS tools."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
import tempfile

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--archive', type=Path, required=True)
p.add_argument('--nbis-directory', type=Path, required=True)
p.add_argument('--detail-tool', type=Path, required=True)
a = p.parse_args()
fixtures = root / 'tests/fixtures'
results = []
with zipfile.ZipFile(a.archive) as archive, tempfile.TemporaryDirectory() as directory:
    published = archive.read('Test_5.0.0/nfiq/execs/nfiq/nfiq_nist.log')
    expected_lines = published.decode().splitlines()
    names = [f'a011{impression}_{finger:02}' for impression in ['r', 'p'] for finger in range(2, 6)]
    for index, name in enumerate(names):
        member = f'Test_5.0.0/nfiq/data/{name}.wsq'
        wsq = Path(directory) / (name + '.wsq')
        source = archive.read(member)
        wsq.write_bytes(source)
        subprocess.run([str(a.nbis_directory / 'imgtools/bin/dwsq'), 'raw', str(wsq), '-raw_out'], check=True, capture_output=True)
        metadata = dict(line.split(maxsplit=1) for line in wsq.with_suffix('.ncm').read_text().splitlines() if line.strip())
        width, height = int(metadata['PIX_WIDTH']), int(metadata['PIX_HEIGHT'])
        raw = wsq.with_suffix('.raw').read_bytes()
        assert len(raw) == width * height
        target = fixtures / (name + '.gray8')
        target.write_bytes(raw)
        output = subprocess.check_output([str(a.detail_tool), str(target), str(width), str(height)], text=True).split()
        published_quality, published_confidence = expected_lines[8 + index * 3 + 2].split()
        assert output[0] == '0' and int(output[1]) == int(published_quality)
        assert abs(float(output[2]) - float(published_confidence)) <= 0.005
        results.append({'id': name, 'raw': target.name, 'width': width, 'height': height, 'dots_per_inch': 500, 'resolution_basis': 'Explicit NBIS NFIQ default 500 ppi for release WSQ files with unspecified PPI', 'native_status': int(output[0]), 'quality_class': int(output[1]), 'confidence': float(output[2]), 'published_quality_class': int(published_quality), 'published_confidence': float(published_confidence), 'source_member': member, 'source_wsq_sha256': hashlib.sha256(source).hexdigest(), 'raw_sha256': hashlib.sha256(raw).hexdigest()})
    (fixtures / 'nfiq1-published.log').write_bytes(published)
(fixtures / 'nfiq1-release-vectors.json').write_text(json.dumps({'source': 'NIST NBIS 5.0.0 test release', 'archive_sha256': hashlib.sha256(a.archive.read_bytes()).hexdigest(), 'published_output_sha256': hashlib.sha256(published).hexdigest(), 'conversion': 'Original NBIS dwsq raw input.wsq -raw_out; decoded grayscale bytes preserved', 'vectors': results}, indent=2) + '\n')
(fixtures / 'nfiq1-release.tsv').write_text(''.join(f"{v['raw']} {v['width']} {v['height']} {v['native_status']} {v['quality_class']} {v['confidence']:.9g}\n" for v in results))
print('Eight original NBIS release vectors agree with the published classes and confidences.')
