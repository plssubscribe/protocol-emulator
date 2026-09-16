"""Mutation checks for public-pin host framing and snapshot protection."""
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
source = (root / 'src/witness_host_spi.v').read_text()
out = root / 'work' / 'host-mutations'
out.mkdir(parents=True, exist_ok=True)
mutants = [
    ('tear_capture_snapshot', 'response(0, snapshot3)',
     "response(0, {2'b0, capture_count, capture_data})", 'capture_overflow_readback_and_reset'),
    ('ignore_crc', 'rx[7:0] != crc', "1'b0", 'host_corrupt_frames_busy_abort_and_reset'),
    ('ignore_frame_length', 'count != 64', "1'b0", 'host_corrupt_frames_busy_abort_and_reset'),
    ('write_while_locked', 'else if (!unlocked)', "else if (1'b0)", 'host_load_execute_and_witness'),
    ('tear_snapshot', 'response(0, snapshot2)', 'response(0, witness_word)',
     'host_synchronized_response_and_atomic_snapshot'),
]
results = []
for name, old, new, test in [('baseline', '', '', 'test_host')] + mutants:
    directory = out / name
    directory.mkdir(exist_ok=True)
    if old and source.count(old) != 1:
        raise SystemExit(f'{name}: mutation site changed')
    rtl = directory / 'witness_host_spi.v'
    rtl.write_text(source.replace(old, new, 1) if old else source)
    xml = directory / 'results.xml'
    xml.unlink(missing_ok=True)
    sources = [root / 'src' / n for n in ('project.v', 'uart_tx.v', 'witness_core.v')]
    sources += [rtl, root / 'test' / 'tb.v']
    command = ['make', '-C', str(root / 'test'),
               'VERILOG_SOURCES=' + ' '.join(map(str, sources)),
               f'SIM_BUILD={directory / "sim_build"}', f'COCOTB_RESULTS_FILE={xml}',
               f'COCOTB_TEST_FILTER={test}']
    with (directory / 'simulation.log').open('w') as log:
        completed = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
    if not xml.exists():
        raise SystemExit(f'{name}: tool failure is not a detected mutant')
    tree = ET.parse(xml)
    failures = tree.findall('.//failure')
    executed = [case for case in tree.findall('.//testcase') if case.find('skipped') is None]
    if not executed or tree.findall('.//error'):
        raise SystemExit(f'{name}: invalid results')
    if name == 'baseline':
        if completed.returncode or failures:
            raise SystemExit('Unmodified host baseline failed')
        continue
    killed = bool(failures) and all(f.get('error_type') == 'AssertionError' for f in failures)
    results.append(dict(mutation=name, test=test, killed=killed))
    print(f'{name}: {"KILLED" if killed else "NOT PROVEN"}')
(out / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
if not all(row['killed'] for row in results):
    raise SystemExit('A host mutant survived or was not detected by an assertion')
