#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Generate ABI-correct OpenCV buffer dispatch from pinned original sources."""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--upstream', type=Path, required=True)
parser.add_argument('--destination', type=Path, required=True)
parser.add_argument('--opencv-build', type=Path, required=True)
args = parser.parse_args()
args.destination.mkdir(parents=True, exist_ok=True)
source = args.upstream / 'modules/core/src'
for operation in ['mean', 'sum']:
    header = (source / (operation + '.simd.hpp')).read_text()
    if operation == 'mean':
        pattern = r'static int (sqsum\w+)\( const (\w+)\* src, const uchar\* mask, (\w+)\* sum, (\w+)\* sqsum, int len, int cn \)\n\{ CV_INSTRUMENT_REGION\(\); return sumsqr_\(src, mask, sum, sqsum, len, cn\); \}'
        def replace(match):
            name, pixel, total, square = match.groups()
            return f'static int {name}(const uchar* src, const uchar* mask, uchar* sum, uchar* sqsum, int len, int cn)\n{{ CV_INSTRUMENT_REGION(); return sumsqr_((const {pixel}*)src, mask, ({total}*)sum, ({square}*)sqsum, len, cn); }}'
        cast = '(SumSqrFunc)'
    else:
        pattern = r'static int (sum\w+)\( const (\w+)\* src, const uchar\* mask, (\w+)\* dst, int len, int cn \)\n\{ CV_INSTRUMENT_REGION\(\); return sum_\(src, mask, dst, len, cn\); \}'
        def replace(match):
            name, pixel, total = match.groups()
            return f'static int {name}(const uchar* src, const uchar* mask, uchar* dst, int len, int cn)\n{{ CV_INSTRUMENT_REGION(); return sum_((const {pixel}*)src, mask, ({total}*)dst, len, cn); }}'
        cast = '(SumFunc)'
    header, count = re.subn(pattern, replace, header)
    if count != 7:
        raise SystemExit(f'Unexpected original OpenCV {operation} dispatch: {count} functions')
    # Removing the casts lets the compiler enforce the dispatch ABI directly.
    header = header.replace(cast, '')
    generated = args.destination / (operation + '.simd.hpp')
    generated.write_text(header)
    (args.destination / (operation + '.dispatch.cpp')).write_text(
        (source / (operation + '.dispatch.cpp')).read_text())
    # OpenCV creates AVX/other CPU dispatch units during configuration. Redirect
    # their absolute include to the same generated header as the baseline unit.
    for unit in (args.opencv_build / 'modules/core').glob(operation + '.*.cpp'):
        text = unit.read_text()
        original_include = (source / (operation + '.simd.hpp')).as_posix()
        if original_include not in text:
            raise SystemExit(f'Missing original OpenCV generated include: {unit}')
        unit.write_text(text.replace(original_include, generated.as_posix()))

# Arithmetic and comparison dispatch share a generic-byte ABI. Adapt all HAL
# entries together so the compiler verifies their tables without pointer casts.
arithmetic = (source / 'arithm.cpp').read_text()
adapters = []
pattern = r'\(BinaryFuncC\)(?:GET_OPTIMIZED\(cv::hal::(\w+)\)|cv::hal::(\w+))'
types = {'8u': 'uchar', '8s': 'schar', '16u': 'ushort', '16s': 'short', '32s': 'int', '32f': 'float', '64f': 'double'}
def adapt(match):
    name = match.group(1) or match.group(2)
    suffix = re.search(r'(8u|8s|16u|16s|32s|32f|64f)$', name).group(1)
    pixel = types[suffix]
    output = 'uchar' if name.startswith('cmp') else pixel
    adapter = 'op_' + name
    adapters.append(f"static void {adapter}(const uchar* a, size_t astep, const uchar* b, size_t bstep, uchar* dst, size_t dstep, int width, int height, void* operation)\n{{ cv::hal::{name}((const {pixel}*)a, astep, (const {pixel}*)b, bstep, ({output}*)dst, dstep, width, height, operation); }}")
    return adapter
arithmetic, count = re.subn(pattern, adapt, arithmetic)
if count != 74:
    raise SystemExit(f'Unexpected OpenCV arithmetic dispatch: {count} functions')
arithmetic = arithmetic.replace('static BinaryFuncC* getMaxTab()', '\n'.join(adapters) + '\nstatic BinaryFuncC* getMaxTab()')
if adapters[0] not in arithmetic:
    raise SystemExit('Missing OpenCV arithmetic adapter insertion point')
(args.destination / 'arithm.cpp').write_text(arithmetic)

math = (source / 'mathfuncs.cpp').read_text()
adapters = []
for suffix, pixel in types.items():
    name = 'iPow' + suffix
    adapters.append(f'static void op_{name}(const uchar* src, uchar* dst, int len, int power) {{ {name}((const {pixel}*)src, ({pixel}*)dst, len, power); }}')
    math = math.replace('(IPowFunc)' + name, 'op_' + name)
math = math.replace('static IPowFunc ipowTab', '\n'.join(adapters) + '\nstatic IPowFunc ipowTab')
adapters = []
for operation in ['sqrt', 'invSqrt']:
    for suffix, pixel in [('32f', 'float'), ('64f', 'double')]:
        name = operation + suffix
        adapters.append(f'static void op_{name}(const void* src, void* dst, int len) {{ hal::{name}((const {pixel}*)src, ({pixel}*)dst, len); }}')
        math = math.replace('(MathFunc)hal::' + name, 'op_' + name)
math = math.replace('static IPowFunc ipowTab', '\n'.join(adapters) + '\nstatic IPowFunc ipowTab')
(args.destination / 'mathfuncs.cpp').write_text(math)

for operation in ['merge', 'split']:
    text = (source / (operation + '.dispatch.cpp')).read_text()
    adapters = []
    for suffix, pixel in [('8u', 'uchar'), ('16u', 'ushort'), ('32s', 'int'), ('64s', 'int64')]:
        name = operation + suffix
        if operation == 'merge':
            adapter = f'static void op_{name}(const uchar** src, uchar* dst, int len, int cn) {{ hal::{name}((const {pixel}**)src, ({pixel}*)dst, len, cn); }}'
        else:
            adapter = f'static void op_{name}(const uchar* src, uchar** dst, int len, int cn) {{ hal::{name}((const {pixel}*)src, ({pixel}**)dst, len, cn); }}'
        adapters.append(adapter)
        text = text.replace('(' + operation.capitalize() + 'Func)GET_OPTIMIZED(cv::hal::' + name + ')', 'op_' + name)
    marker = 'static ' + operation.capitalize() + 'Func get' + operation.capitalize() + 'Func(int depth)'
    if marker not in text:
        raise SystemExit('Missing OpenCV ' + operation + ' dispatch insertion')
    text = text.replace(marker, '\n'.join(adapters) + '\n' + marker)
    (args.destination / (operation + '.dispatch.cpp')).write_text(text)

dxt = (source / 'dxt.cpp').read_text()
for operation in ['DFT', 'RealDFT', 'CCSIDFT']:
    for suffix, pixel in [('32f', 'Complexf' if operation == 'DFT' else 'float'), ('64f', 'Complexd' if operation == 'DFT' else 'double')]:
        old = f'static void {operation}_{suffix}(const OcvDftOptions & c, const {pixel}* src, {pixel}* dst)\n{{\n    {operation}(c, src, dst);\n}}'
        new = f'static void {operation}_{suffix}(const OcvDftOptions & c, const void* src, void* dst)\n{{\n    {operation}(c, (const {pixel}*)src, ({pixel}*)dst);\n}}'
        if old not in dxt: raise SystemExit('Missing original DFT wrapper')
        dxt = dxt.replace(old, new).replace('(DFTFunc)' + operation + '_' + suffix, operation + '_' + suffix)
pattern = r'static void (I?DCT)_(32f|64f)\(const OcvDftOptions & c, const (float|double)\* src, size_t src_step, (?:float|double)\* dft_src, (?:float|double)\* dft_dst,\n\s+(?:float|double)\* dst, size_t dst_step, const (Complexf|Complexd)\* dct_wave\)\n\{\n    I?DCT\(c, src, src_step, dft_src, dft_dst, dst, dst_step, dct_wave\);\n\}'
def adapt_dct(match):
    operation, suffix, pixel, wave = match.groups()
    return f'static void {operation}_{suffix}(const OcvDftOptions & c, const void* src, size_t src_step, void* dft_src, void* dft_dst, void* dst, size_t dst_step, const void* dct_wave)\n{{ {operation}(c, (const {pixel}*)src, src_step, ({pixel}*)dft_src, ({pixel}*)dft_dst, ({pixel}*)dst, dst_step, (const {wave}*)dct_wave); }}'
dxt, count = re.subn(pattern, adapt_dct, dxt)
if count != 4: raise SystemExit('Unexpected DCT wrappers')
dxt = dxt.replace('(DCTFunc)', '')
(args.destination / 'dxt.cpp').write_text(dxt)

norm = (source / 'norm.cpp').read_text()
adapters = []
result_types = {'8u': ('int', 'int', 'int'), '8s': ('int', 'int', 'int'), '16u': ('int', 'int', 'double'), '16s': ('int', 'int', 'double'), '32s': ('int', 'double', 'double'), '32f': ('float', 'double', 'double'), '64f': ('double', 'double', 'double')}
for suffix, pixel in types.items():
    for operation, total in zip(['Inf', 'L1', 'L2'], result_types[suffix]):
        for difference in [False, True]:
            name = 'norm' + ('Diff' if difference else '') + operation + '_' + suffix
            if difference:
                adapters.append(f'static int op_{name}(const uchar* a, const uchar* b, const uchar* mask, uchar* result, int len, int cn) {{ return {name}((const {pixel}*)a, (const {pixel}*)b, mask, ({total}*)result, len, cn); }}')
                cast = 'NormDiffFunc'
            else:
                adapters.append(f'static int op_{name}(const uchar* a, const uchar* mask, uchar* result, int len, int cn) {{ return {name}((const {pixel}*)a, mask, ({total}*)result, len, cn); }}')
                cast = 'NormFunc'
            pattern = r'\(' + cast + r'\)(?:GET_OPTIMIZED\(' + name + r'\)|' + name + r')'
            norm, count = re.subn(pattern, 'op_' + name, norm)
            if count != 1: raise SystemExit('Unexpected original norm table: ' + name)
norm = norm.replace('static NormFunc getNormFunc', '\n'.join(adapters) + '\nstatic NormFunc getNormFunc')
(args.destination / 'norm.cpp').write_text(norm)

minimum = (source / 'minmax.cpp').read_text()
adapters = []
for suffix, pixel in types.items():
    name = 'minMaxIdx_' + suffix
    total = pixel if suffix in ['32f', '64f'] else 'int'
    adapters.append(f'static void op_{name}(const uchar* src, const uchar* mask, int* minimum, int* maximum, size_t* minidx, size_t* maxidx, int len, size_t start) {{ {name}((const {pixel}*)src, mask, ({total}*)minimum, ({total}*)maximum, minidx, maxidx, len, start); }}')
    minimum = minimum.replace('(MinMaxIdxFunc)GET_OPTIMIZED(' + name + ')', 'op_' + name)
minimum = minimum.replace('static MinMaxIdxFunc getMinmaxTab', '\n'.join(adapters) + '\nstatic MinMaxIdxFunc getMinmaxTab')
(args.destination / 'minmax.cpp').write_text(minimum)
