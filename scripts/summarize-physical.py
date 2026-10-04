"""Extract reported physical metrics without treating missing checks as passes."""
import argparse
import hashlib
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('artifacts', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--require-clean', action='store_true',
                    help='Fail unless final timing and electrical metrics are present and clean.')
args = parser.parse_args()
run = args.artifacts / 'GDS_logs/runs/wokwi'
states = sorted(run.glob('*/state_out.json'), key=lambda p: int(p.parent.name.split('-')[0]))
if not states:
    raise SystemExit('No LibreLane state reports found in the supplied artifacts.')
state = states[-1]
metrics = json.loads(state.read_text()).get('metrics', {})
keys = ['design__instance__count', 'design__instance__area', 'design__die__area',
        'design__core__area', 'design__instance__area__stdcell',
        'design__instance__count__stdcell', 'design__instance__utilization__stdcell',
        'design__max_slew_violation__count', 'design__max_fanout_violation__count',
        'design__max_cap_violation__count',
        'design__instance__count__class:fill_cell', 'timing__setup__ws',
        'timing__hold__ws', 'timing__setup_vio__count', 'timing__hold_vio__count',
        'route__drc_errors', 'magic__drc_error__count', 'design__lvs_error__count',
        'antenna__violating__nets', 'antenna__violating__pins']
report = dict(last_state=str(state.relative_to(args.artifacts)),
              state_sha256=hashlib.sha256(state.read_bytes()).hexdigest(),
              metrics={key: metrics.get(key) for key in keys},
              timing_corners={key: value for key,value in metrics.items()
                              if key.startswith(('timing__', 'design__max_')) and '__corner:' in key},
              missing_metrics=[key for key in keys if key not in metrics],
              scope='Reported metrics only. Missing values are not passes; review workflow, SDC, precheck and simulation separately.')
def finite(value):
    if isinstance(value, dict):
        return {key: finite(item) for key, item in value.items()}
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value

report['nonfinite_metrics'] = [key for key, value in report['timing_corners'].items()
                               if isinstance(value, float) and not math.isfinite(value)]
report = finite(report)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
print(json.dumps(report['metrics'], indent=2))

if args.require_clean:
    required_zero = ['timing__setup_vio__count', 'timing__hold_vio__count',
                     'design__max_slew_violation__count',
                     'design__max_fanout_violation__count',
                     'design__max_cap_violation__count',
                     'route__drc_errors', 'magic__drc_error__count',
                     'design__lvs_error__count', 'antenna__violating__nets',
                     'antenna__violating__pins']
    failures = [key for key in required_zero if report['metrics'].get(key) != 0]
    for key in ['timing__setup__ws', 'timing__hold__ws']:
        value = report['metrics'].get(key)
        if value is None or value < 0:
            failures.append(key)
    if 'reportmanufacturability' not in state.parent.name:
        failures.append('final manufacturability state absent')
    if failures:
        raise SystemExit('Physical acceptance failed: ' + ', '.join(failures))
    print('Reported timing, electrical and geometry metrics are clean. Separate gate/precheck jobs remain required.')
