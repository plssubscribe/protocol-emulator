"""Reproducible generic synthesis; no PDK area or timing claim."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--integrated', action='store_true')
args = parser.parse_args()
top = 'tt_um_protocol_emulator' if args.integrated else 'witness_core'
folder = 'synthesis-top' if args.integrated else 'synthesis'
sources = ['src/witness_core.v']
if args.integrated:
    sources += ['src/witness_host_spi.v', 'src/uart_tx.v', 'src/project.v']
out = root / 'work' / folder
out.mkdir(parents=True, exist_ok=True)
tool = shutil.which('yowasp-yosys') or shutil.which('yosys')
if not tool:
    raise SystemExit('Install yosys or test/synthesis-requirements.txt in the active environment.')
for name in (f'{top}.json', f'{top}.v', 'summary.json'):
    (out / name).unlink(missing_ok=True)
commands = (f'read_verilog {" ".join(sources)}; synth -top {top}; check -assert; '
            f'write_verilog -noattr work/{folder}/{top}.v; '
            f'write_json work/{folder}/{top}.json')
with (out / 'yosys.log').open('w') as log:
    subprocess.run([tool, '-Q', '-T', '-p', commands], cwd=root, stdout=log,
                   stderr=subprocess.STDOUT, check=True)
data = json.loads((out / f'{top}.json').read_text())
def count_cells(module_name):
    result = Counter()
    for cell in data['modules'][module_name]['cells'].values():
        if cell['type'] in data['modules']:
            result.update(count_cells(cell['type']))
        else:
            result[cell['type']] += 1
    return result
counts = count_cells(top)
if not counts:
    raise SystemExit('Synthesis produced no cells')
summary = dict(top=top, kind='generic synthesis, not CMOS5L mapping or timing',
               tool=subprocess.check_output([tool, '-V'], text=True).strip(),
               source_sha256=sha256((root / 'src/witness_core.v').read_bytes()).hexdigest(),
               source_hashes={path: sha256((root / path).read_bytes()).hexdigest() for path in sources},
               cells=sum(counts.values()), flip_flops=sum(n for t, n in counts.items() if 'DFF' in t),
               cells_by_type=dict(sorted(counts.items())), structural_check='passed')
(out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
