#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Record independent quality results and verify NIST's release example scores."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--nfiq1-tool', type=Path, required=True, help='Original NBIS nfiq CLI')
p.add_argument('--nfiq1-detail-tool', type=Path, required=True, help='Separately linked original NBIS API tool')
p.add_argument('--nfiq2-tool', type=Path, required=True, help='Separately built original NFIQ2 API tool')
a = p.parse_args()
fixtures = root / 'tests/fixtures'
manifest = json.loads((fixtures / 'provenance.json').read_text())
original, unified, cli = [], [], []
for item in manifest['images']:
    path = fixtures / item['raw']
    output = subprocess.check_output([str(a.nfiq1_tool), '-v', '-raw', '512,512,8,500', str(path)], text=True)
    detail = subprocess.check_output([str(a.nfiq1_detail_tool), str(path)], text=True).strip()
    assert int(output.splitlines()[-1].split()[0]) == int(detail.split()[1])
    cli.append({'image': path.name, 'stdout': output, 'stdout_sha256': hashlib.sha256(output.encode()).hexdigest()})
    original.append(path.name + ' ' + detail)
    result = subprocess.check_output([str(a.nfiq2_tool), str(path)], text=True).split()
    unified.append(path.name + ' ' + ' '.join(result[:3]))
(fixtures / 'nfiq1-reference.tsv').write_text('\n'.join(original) + '\n')
(fixtures / 'nfiq2-reference.tsv').write_text('\n'.join(unified) + '\n')
(fixtures / 'nfiq1-official-cli.json').write_text(json.dumps({'source_archive_sha256': '0adf8ab0f6b0e4208de50ca00ba21d3d77112ecd66288757ddfed21f6bee92c3', 'command': 'nfiq -v -raw 512,512,8,500 <capture.gray8>', 'results': cli}, indent=2) + '\n')
release = []
for pgm in sorted((root / 'native/nfiq2/upstream/examples/images').glob('*.pgm')):
    data = pgm.read_bytes()
    header = re.match(rb'P5\s+(\d+)\s+(\d+)\s+255\s', data)
    assert header
    width, height = map(int, header.groups())
    pixels = data[header.end():]
    assert len(pixels) == width * height
    raw = fixtures / (pgm.stem + '.gray8')
    raw.write_bytes(pixels)
    expected_file = pgm.parent.parent / 'output' / (pgm.stem + '_output.txt')
    expected = int(re.search(r'UnifiedQualityScore: (\d+)', expected_file.read_text()).group(1))
    actual = subprocess.check_output([str(a.nfiq2_tool), str(raw), str(width), str(height)], text=True).split()
    assert actual[:3] == ['0', str(expected), '0'], (pgm.name, expected, actual)
    release.append({'id': pgm.stem, 'raw': raw.name, 'width': width, 'height': height, 'dots_per_inch': 500, 'score': expected, 'source_pgm_sha256': hashlib.sha256(data).hexdigest(), 'raw_sha256': hashlib.sha256(pixels).hexdigest(), 'expected_output_sha256': hashlib.sha256(expected_file.read_bytes()).hexdigest()})
(fixtures / 'nfiq2-release-vectors.json').write_text(json.dumps({'source': 'NIST NFIQ2 v2.3.0 release examples', 'upstream_commit': '76b8c4e0b0541f3deab832b1a496e524edc0b5b6', 'vectors': release}, indent=2) + '\n')
(fixtures / 'nfiq2-release.tsv').write_text(''.join(f"{v['raw']} {v['width']} {v['height']} 0 {v['score']} 0\n" for v in release))
print('Recorded 20 independent SD04 results and verified all five NIST release examples.')
