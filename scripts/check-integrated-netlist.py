"""Refuse to reuse a generic netlist if its RTL input hashes have changed."""
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
summary = root / 'work' / 'synthesis-top' / 'summary.json'
if not summary.exists():
    raise SystemExit('Run make synth-top-check to generate the integrated netlist first.')
record = json.loads(summary.read_text())
for source, expected in record['source_hashes'].items():
    if hashlib.sha256((root / source).read_bytes()).hexdigest() != expected:
        raise SystemExit(f'{source} changed; regenerate with make synth-top-check.')
if not (summary.parent / 'tt_um_protocol_emulator.v').exists():
    raise SystemExit('Netlist missing; run make synth-top-check.')
print('Integrated netlist RTL hashes match the current source.')
