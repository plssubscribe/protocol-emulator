"""Render an actual sampled failure trace as a compact standalone SVG waveform."""
import hashlib
import html
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / 'work' / 'i2c-witness.json'
record = json.loads(source.read_text())
case = record['first_failure']
trace = case['trace']
hold_start = next(row['cycle'] for row in trace if row['target_low'] & 1)
release = next(row['cycle'] for row in trace[hold_start:] if not row['target_low'] & 1)
start, end = max(0, hold_start-5), min(len(trace)-1, release+25)
left, scale = 205, 760/(end-start)
def x(cycle):
    return left + (cycle-start)*scale
parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="410" viewBox="0 0 1000 410">',
         '<rect width="1000" height="410" fill="#101827"/>',
         '<g font-family="Arial, sans-serif" fill="#e6edf7">']
def text(xp, yp, message, size=14, color='#e6edf7'):
    parts.append(f'<text x="{xp:.1f}" y="{yp:.1f}" font-size="{size}" fill="{color}">{html.escape(message)}</text>')
text(25, 34, f"A {case['stretch']}-cycle hold exposes a shortened I²C clock", 23)
text(25, 58, 'Actual RTL pin trace · accelerated digital fixture · ideal pull-ups', 14, '#9eafc7')
for cycle in range(start, end+1):
    if cycle % 5 == 0:
        parts.append(f'<path d="M{x(cycle):.1f},85 V325" stroke="#26344a"/>')
        text(x(cycle)-6, 345, str(cycle), 11, '#9eafc7')
lanes = [('Controller release SCL', lambda r: not r['controller_low'] & 1, '#86b7ff'),
         ('Target release SCL', lambda r: not r['target_low'] & 1, '#be9cff'),
         ('Resolved SCL', lambda r: bool(r['bus'] & 1), '#ffb86b'),
         ('Resolved SDA', lambda r: bool(r['bus'] & 2), '#66dbb7')]
for index, (label, signal, color) in enumerate(lanes):
    top = 98 + index*56
    text(25, top+14, label, 14, color)
    level = top if signal(trace[start]) else top+26
    path = f'M{x(start):.1f},{level}'
    for cycle in range(start+1, end+1):
        level = top if signal(trace[cycle]) else top+26
        path += f' H{x(cycle):.1f} V{level}'
    parts.append(f'<path d="{path}" stroke="{color}" stroke-width="2.5" fill="none"/>')
parts.append(f'<path d="M{x(release):.1f},84 V325" stroke="#ff6f7c" stroke-dasharray="4 4"/>')
text(25, 373, f"First resolved SCL high: {case['high_widths'][0]} cycle(s); configured controller high: {case['high']} cycles.", 16)
text(25, 396, 'The faulty controller counts through the hold. PC 5 then records a missed data expectation.', 14, '#9eafc7')
parts += ['</g>', f'<!-- Source SHA256: {hashlib.sha256(source.read_bytes()).hexdigest()} -->', '</svg>']
output = root / 'docs' / 'images' / 'i2c-stretch-boundary.svg'
output.write_text('\n'.join(parts)+'\n')
print(output)
