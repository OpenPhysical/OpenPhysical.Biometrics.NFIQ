#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Consume both packages outside the repository and check the missing-library path."""
import argparse,subprocess,tempfile,zipfile,hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from runtime_manifest import load_runtimes, native_file
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=ET.parse(ROOT/'Directory.Build.props').findtext('./PropertyGroup/Version'));p.add_argument('--require-all-runtimes', action='store_true');a=p.parse_args()
feed=ROOT/'artifacts/packages'
for algorithm in ('nfiq1', 'nfiq2'):
 package=feed/f'OpenPhysical.Biometrics.{algorithm.upper()}.{a.version}.nupkg'
 with zipfile.ZipFile(package) as z:
  assert z.read("runtimes.props") == (ROOT / "runtimes.props").read_bytes(), "Packaged catalog must match the release source."
  if a.require_all_runtimes:
   for entry in load_runtimes():
    assert f"runtimes/{entry['rid']}/native/{native_file(entry, algorithm)}" in z.namelist(), entry['rid']
  assert not any('/fixtures/' in n or n.endswith('.gray8') for n in z.namelist())
  seen = set()
  for name in z.namelist():
   if '/native/libopencv_' in name:
    key = (str(Path(name).parent), hashlib.sha256(z.read(name)).digest())
    assert key not in seen, f'Duplicate OpenCV payload: {name}'
    seen.add(key)
with tempfile.TemporaryDirectory(prefix='nfiq-consumer-') as temp:
 d=Path(temp)
 (d/'Consumer.csproj').write_text(f'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><RestorePackagesPath>{d / "packages"}</RestorePackagesPath></PropertyGroup><ItemGroup><PackageReference Include="OpenPhysical.Biometrics.NFIQ1" Version="{a.version}"/><PackageReference Include="OpenPhysical.Biometrics.NFIQ2" Version="{a.version}"/></ItemGroup></Project>')
 (d/'NuGet.Config').write_text(f'<configuration><packageSources><clear/><add key="local" value="{feed}"/><add key="nuget" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
 (d/'Program.cs').write_text('''using OpenPhysical.Biometrics.NFIQ1;
using OpenPhysical.Biometrics.NFIQ2;
if(args is ["missing"]){try{_=new Nfiq1Engine();return 3;}catch(DllNotFoundException){return 0;}}
var pixels=File.ReadAllBytes(args[0]);
var first=new Nfiq1Engine().Assess(pixels,512,512,500);
using var second=new Nfiq2Engine();
var score=second.Assess(pixels,512,512,500);
return first.QualityClass is >=1 and <=5 && score.UnifiedQualityScore is >=0 and <=100 ? 0 : 2;
''')
 def run(*args):subprocess.run(args,cwd=d,check=True)
 run('dotnet','build','Consumer.csproj','-c','Release','-m:1','-p:UseSharedCompilation=false')
 dll=d/'bin/Release/net10.0/Consumer.dll'
 run('dotnet',str(dll),str(ROOT/'tests/fixtures/f0005_03.gray8'))
 libraries=[p for p in dll.parent.rglob('*') if p.is_file() and 'openphysical_nfiq1' in p.name]
 assert libraries,'No packaged NFIQ1 native runtime was copied.'
 for lib in libraries:lib.rename(lib.with_name(lib.name+'.hidden'))
 run('dotnet',str(dll),'missing')
print('Isolated package consumer, fixture exclusions and missing-runtime checks passed.')
