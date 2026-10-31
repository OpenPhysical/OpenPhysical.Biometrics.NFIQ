#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Verify the twenty attributed, full-frame 500 ppi grayscale fixtures offline."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'tests/fixtures'
manifest=json.loads((root/'provenance.json').read_text())
assert len(manifest['images'])==20
for image in manifest['images']:
 pixels=(root/image['raw']).read_bytes()
 assert len(pixels)==512*512 and image['width']==512 and image['height']==512 and image['dots_per_inch']==500
 assert hashlib.sha256(pixels).hexdigest()==image['raw_sha256']
assert {image['impression'] for image in manifest['images']}=={'first','second'}
print('SD04 fixture integrity and pair metadata verified.')

release=json.loads((root/'nfiq2-release-vectors.json').read_text())
assert len(release['vectors'])==5
for vector in release['vectors']:
 pixels=(root/vector['raw']).read_bytes()
 assert len(pixels)==vector['width']*vector['height']
 assert hashlib.sha256(pixels).hexdigest()==vector['raw_sha256']
print('NIST NFIQ2 release example pixels verified.')

release1=json.loads((root/'nfiq1-release-vectors.json').read_text())
assert len(release1['vectors'])==8
for vector in release1['vectors']:
 pixels=(root/vector['raw']).read_bytes()
 assert len(pixels)==vector['width']*vector['height']
 assert hashlib.sha256(pixels).hexdigest()==vector['raw_sha256']
print('NBIS NFIQ1 release example pixels verified.')

reference=json.loads((root/'reference-provenance.json').read_text())
for name, expected in reference['output_sha256'].items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected
print('Committed independent reference outputs verified.')

negative=json.loads((root/'negative/manifest.json').read_text())
for fixture in negative['fixtures']:
 assert hashlib.sha256((root/'negative'/fixture['filename']).read_bytes()).hexdigest()==fixture['sha256']
print('Generated poor-capture and malformed-input fixtures verified.')
