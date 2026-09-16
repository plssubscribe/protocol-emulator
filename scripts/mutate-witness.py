"""Confirm selected intentional RTL defects are killed by named regression tests."""
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
source = (root / 'src/witness_core.v').read_text()
out = root / 'work' / 'mutations'
out.mkdir(parents=True, exist_ok=True)
mutants = [
    ('capture_wrong_pin', 'pins_in[a[2:0]]', 'pins_in[0]',
     'timed_capture_capacity_and_lifecycle'),
    ('capture_overwrite_full', 'opcode == 5 && capture_count == 32',
     'opcode == 5 && capture_count == 33', 'timed_capture_capacity_and_lifecycle'),
    ('miss_last_sample', 'opcode == 2 && (pins_in & b) == a',
     "opcode == 2 && (pins_in & b) == a && age != duration - 1'b1",
     'inclusive_deadlines_and_random_programs'),
    ('ignore_input_mask', '(pins_in & b) == a', 'pins_in == a',
     'inclusive_deadlines_and_random_programs'),
    ('wrong_output_enable', 'pins_oe <= next_word[7:0];',
     'pins_oe <= ~next_word[7:0];', 'programmed_uart_independent_wire_oracle'),
    ('allow_live_write', 'end else if (running) begin',
     'end else if (running) begin\n            if (load_valid) memory[load_addr] <= load_word;',
     'loader_reset_abort_and_faults'),
]
results = []
# Baseline must pass through the same invocation path before failures mean anything.
for name, old, new, test in [('baseline', '', '', '')] + mutants:
    directory = out / name
    directory.mkdir(exist_ok=True)
    if old and source.count(old) != 1:
        raise SystemExit(f'{name}: expected exactly one mutation site')
    rtl = directory / 'witness_core.v'
    rtl.write_text(source.replace(old, new, 1) if old else source)
    xml = directory / 'results.xml'
    xml.unlink(missing_ok=True)
    command = ['make', '-C', str(root / 'test' / 'engine'), f'CORE_SOURCE={rtl}',
               f'SIM_BUILD={directory / "sim_build"}', f'COCOTB_RESULTS_FILE={xml}',
               f'COCOTB_TEST_FILTER={test}']
    with (directory / 'simulation.log').open('w') as log:
        completed = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
    if not xml.exists():
        raise SystemExit(f'{name}: tool failure, not a detected mutation; inspect simulation.log')
    tree = ET.parse(xml)
    cases = [c for c in tree.findall('.//testcase') if c.find('skipped') is None]
    failures = tree.findall('.//failure')
    errors = tree.findall('.//error')
    if not cases or errors:
        raise SystemExit(f'{name}: invalid test result')
    if name == 'baseline':
        if completed.returncode or failures:
            raise SystemExit('Unmodified baseline failed; mutation score is invalid')
        continue
    # A compile error cannot count as a killed mutant: only assertion failures do.
    killed = bool(failures) and all(f.get('error_type') == 'AssertionError' for f in failures)
    results.append(dict(mutation=name, test=test, killed=killed,
                        failure_types=[f.get('error_type') for f in failures]))
    print(f'{name}: {"KILLED" if killed else "NOT PROVEN"}')
(out / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
if not all(r['killed'] for r in results):
    raise SystemExit('Not every selected mutation was detected by an assertion')
