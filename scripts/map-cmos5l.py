"""Pinned CMOS5L library mapping only; no floorplan or physical timing claim."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request

root = Path(__file__).resolve().parents[1]
out = root / 'work/cmos5l-mapping'
out.mkdir(parents=True, exist_ok=True)
(out / 'summary.json').unlink(missing_ok=True)
revision = 'ae7613984daf3ac2b14897321399df497278068f'
library = 'sg13cmos5l_stdcell_typ_1p20V_25C.lib'
url = f'https://raw.githubusercontent.com/IHP-GmbH/ihp-sg13cmos5l/{revision}/libs.ref/sg13cmos5l_stdcell/lib/{library}'
lib = out / library
if not lib.exists():
    with urllib.request.urlopen(url, timeout=60) as response:
        lib.write_bytes(response.read())
if hashlib.sha256(lib.read_bytes()).hexdigest() != 'ed101ac8140270f1e376ef4eb45b12e26c44db109e26aad69b1b6f89e7428cf0':
    raise SystemExit('Pinned library checksum mismatch; mapping refused.')
model_url = f'https://raw.githubusercontent.com/IHP-GmbH/ihp-sg13cmos5l/{revision}/libs.ref/sg13cmos5l_stdcell/verilog/sg13cmos5l_stdcell.v'
with urllib.request.urlopen(model_url, timeout=60) as response:
    (out / 'cells.v').write_bytes(response.read())
tool = shutil.which('yowasp-yosys') or shutil.which('yosys')
if not tool:
    raise SystemExit('Activate the environment with synthesis requirements installed.')
sources = ['src/project.v', 'src/uart_tx.v', 'src/witness_core.v', 'src/witness_host_spi.v']
exclude_url = f'https://raw.githubusercontent.com/IHP-GmbH/ihp-sg13cmos5l/{revision}/libs.tech/librelane/sg13cmos5l_stdcell/synth_exclude.cells'
with urllib.request.urlopen(exclude_url, timeout=60) as response:
    excludes = response.read().decode()
(out / 'synth_exclude.cells').write_text(excludes)
excluded_cells = [line.strip() for line in excludes.splitlines() if line.strip() and not line.startswith('#')]
exclude_flags = ' '.join('-dont_use ' + cell for cell in excluded_cells)
relative_lib = str(lib.relative_to(root))
commands = f'''read_liberty -lib {relative_lib};
read_verilog {' '.join(sources)};
synth -top tt_um_protocol_emulator -flatten -noabc;
dfflibmap -liberty {relative_lib} {exclude_flags};
abc -liberty {relative_lib} {exclude_flags};
clean;
delete t:$scopeinfo;
check -assert;
stat -liberty {relative_lib};
write_verilog -noattr -noexpr work/cmos5l-mapping/mapped.v;
write_json work/cmos5l-mapping/mapped.json;
'''
(out / 'map.ys').write_text(commands)
(out / 'summary.json').unlink(missing_ok=True)
with (out / 'yosys.log').open('w') as log:
    subprocess.run([tool, '-Q', '-T', '-s', 'work/cmos5l-mapping/map.ys'], cwd=root,
                   stdout=log, stderr=subprocess.STDOUT, check=True)
data = json.loads((out / 'mapped.json').read_text())
counts = {}
area = 0.0
for cell in data['modules']['tt_um_protocol_emulator']['cells'].values():
    kind = cell['type']
    if kind not in data['modules'] or 'area' not in data['modules'][kind]['attributes']:
        raise SystemExit(f'Unmapped or uncharacterized cell: {kind}')
    if kind in excluded_cells:
        raise SystemExit(f'Excluded cell was used: {kind}')
    counts[kind] = counts.get(kind, 0) + 1
    area += float(data['modules'][kind]['attributes']['area'])
summary = dict(scope='CMOS5L typical-corner library mapping; not physical implementation',
    tool=subprocess.check_output([tool, '-V'], text=True).strip(),
    process_revision=revision, library_url=url, excluded_cells=excluded_cells,
    library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),
    model_sha256=hashlib.sha256((out / 'cells.v').read_bytes()).hexdigest(),
    source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},
    cells=sum(counts.values()), cell_area_um2=round(area, 4), cells_by_type=counts,
    clock_target_ns=20, timing_constraint_applied=False,
    checks_run=['library mapping', 'Yosys structural check', 'mapped-cell completeness'],
    checks_not_run=['placement', 'routing', 'static timing', 'DRC', 'LVS', 'PDK gate simulation'])
(out / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2))
