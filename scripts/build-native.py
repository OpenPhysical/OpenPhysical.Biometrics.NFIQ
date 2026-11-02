#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build one pinned algorithm for the current runtime, then stage its native assets."""
import argparse,hashlib,json,platform,shutil,subprocess,os,sys
from pathlib import Path
from runtime_manifest import load_runtimes
from native_assets import deduplicate_opencv, stage_runtime_licenses
ROOT=Path(__file__).resolve().parents[1]
def run(*args):subprocess.run(list(map(str,args)),check=True,cwd=ROOT)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--algorithm',choices=['nfiq1','nfiq2'],required=True);p.add_argument('--rid');p.add_argument('--tests',action='store_true');p.add_argument('--sanitizer',choices=['asan','ubsan']);a=p.parse_args()
 system={'Darwin':'osx','Linux':'linux','Windows':'win'}[platform.system()];arch={'arm64':'arm64','aarch64':'arm64','AMD64':'x64','x86_64':'x64'}[platform.machine()];rid=f'{system}-{arch}'
 if a.rid and a.rid!=rid:p.error('Build each RID on a native runner of the same architecture.')
 if rid not in {entry['rid'] for entry in load_runtimes()}:p.error('Unsupported runtime.')
 run(sys.executable, ROOT/'scripts/verify-nfiq1-source.py')
 if a.algorithm=='nfiq2':
  upstream=ROOT/'native/nfiq2/upstream'
  expected={'':'76b8c4e0b0541f3deab832b1a496e524edc0b5b6','fingerjetfxose':'d67f329511d65c94d74adacb0678680723d04094','digestpp':'873b5bbab87a8a62ea7bf2ea8d26733181a2fe8d','opencv':'71d3237a093b60a27601c20e9ee6c3e52154e8b1'}
  for relative,commit in expected.items():
   source=upstream/relative
   actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
   if actual!=commit:raise SystemExit(f'Unexpected upstream commit: {relative}')
   subprocess.run(['git','-C',str(source),'diff','--exit-code','--quiet'],check=True)
 diagnostic=ROOT/'artifacts/sanitizers'/a.algorithm/rid
 if a.sanitizer:
  diagnostic.mkdir(parents=True,exist_ok=True)
  for previous in diagnostic.glob(a.sanitizer+'.*'):previous.unlink()
 if a.sanitizer=='ubsan':os.environ['UBSAN_OPTIONS']=f'halt_on_error=1:print_stacktrace=1:log_path={diagnostic}/ubsan'
 if a.sanitizer=='asan':os.environ['ASAN_OPTIONS']=os.environ.get('ASAN_OPTIONS','detect_leaks=0' if system=='osx' else 'detect_leaks=1')+f':log_path={diagnostic}/asan'
 os.environ.setdefault('SOURCE_DATE_EPOCH','1727740800')
 tests=a.tests or bool(a.sanitizer);suffix=a.sanitizer or ('tests' if tests else 'release');build=ROOT/'artifacts/native'/f'{a.algorithm}-{rid}-{suffix}';stage=ROOT/'artifacts/runtimes'/a.algorithm/rid/'native'
 flags=['-DCMAKE_BUILD_TYPE=Release',f'-DBUILD_TESTING={"ON" if tests else "OFF"}','-DCMAKE_POSITION_INDEPENDENT_CODE=ON']
 if system=='osx':flags+=['-DCMAKE_OSX_DEPLOYMENT_TARGET=12.0']
 if system=='win':flags+=['-G','Ninja','-DCMAKE_C_COMPILER=gcc','-DCMAKE_CXX_COMPILER=g++']
 if a.sanitizer:
  sanitizer={'asan':'address','ubsan':'undefined'}[a.sanitizer];key='OP_NBIS_SANITIZERS' if a.algorithm=='nfiq1' else 'OP_SANITIZER';flags+=[f'-D{key}={sanitizer}']
 run('cmake','-S',ROOT/'native'/a.algorithm,'-B',build,*flags)
 run('cmake','--build',build,'--config','Release','--parallel','4')
 if tests:
  try:run('ctest','--test-dir',build,'-C','Release','--output-on-failure')
  finally:
   if a.sanitizer:
    for report in diagnostic.glob(a.sanitizer+'.*'):print(report.read_text(errors='replace'),flush=True)
 else:
  stage.mkdir(parents=True,exist_ok=True);run('cmake','--install',build,'--config','Release','--prefix',stage)
  if system!='win' and a.algorithm=='nfiq2':deduplicate_opencv(stage)
  if system=='win' and a.algorithm=='nfiq2':
   toolchain=Path(shutil.which('g++')).parent
   for name in ['libstdc++-6.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll']:
    dependency=toolchain/name
    if not dependency.is_file():raise SystemExit(f'Missing compiler runtime dependency: {name}')
    shutil.copy2(dependency,stage/name)
   licenses=toolchain.parent/'share/licenses'
   if not licenses.is_dir():raise SystemExit('Missing compiler runtime license directory.')
   stage_runtime_licenses(licenses,stage/'licenses')


if __name__=='__main__':main()
