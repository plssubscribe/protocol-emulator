"""Bounded public-interface safety checks; this is not full functional proof."""
import json
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
out = root / 'work' / 'formal'
out.mkdir(parents=True, exist_ok=True)
(out / 'summary.json').unlink(missing_ok=True)
tool = shutil.which('yowasp-yosys') or shutil.which('yosys')
if not tool:
    raise SystemExit('Install the optional synthesis requirements first.')
commands = ('read_verilog -formal -sv src/witness_core.v test/formal/witness_safety.v; '
            'prep -top witness_safety -flatten; memory_map; opt; async2sync; chformal -lower; '
            'sat -seq 12 -set-assumes -set-def-inputs -set-init-def '
            '-prove-asserts -verify -timeout 30 -dump_vcd work/formal/counterexample.vcd; '
            'sat -seq 8 -set-assumes -set-def-inputs -set-init-def '
            '-set-at 8 done 1 -set-at 8 status 1 -timeout 30 '
            '-dump_vcd work/formal/reachable-timeout.vcd')
with (out / 'yosys.log').open('w') as log:
    subprocess.run([tool, '-Q', '-T', '-p', commands], cwd=root, stdout=log,
                   stderr=subprocess.STDOUT, check=True)
if 'SUCCESS!' not in (out / 'yosys.log').read_text():
    raise SystemExit('Solver did not report success; inspect work/formal/yosys.log')
if 'SAT solving finished - model found:' not in (out / 'yosys.log').read_text():
    raise SystemExit('Timeout reachability not established')
summary = dict(result='passed', depth=12, timeout_reachable_by_step=8,
               kind='bounded safety, not induction',
               assumptions='one initial synchronous reset; defined arbitrary inputs and initial state',
               properties=['capture count never exceeds 32', 'idle releases enables', 'done excludes running',
                           'synchronous reset clears outputs and execution',
                           'abort stops and releases', 'terminal record stays stable until restart/reset',
                           'load wins over simultaneous start'])
(out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
