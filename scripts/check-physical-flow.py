"""Validate the pinned physical plugin without running implementation tools.

Run with LibreLane 3.0.0rc1 installed: python scripts/check-physical-flow.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from librelane.plugins import discovered_plugins
from librelane.flows.classic import Classic
from librelane.flows.flow import Flow

assert 'librelane_plugin_witness' in discovered_plugins
flow = Flow.factory.get('WitnessClassic')
assert flow is not None
ids = [step.id for step in flow.Steps]
assert [id for id in ids if not id.startswith('Witness.')] == [
    step.id for step in Classic.Steps
]
assert flow.config_vars == Classic.config_vars
for key, value in Classic.gating_config_vars.items():
    assert flow.gating_config_vars[key] == value
assert flow.gating_config_vars['Witness.RepairLateLoads*'] == ['RUN_POST_GRT_DESIGN_REPAIR']
assert flow.gating_config_vars['Witness.RerouteLateLoads*'] == ['RUN_DRT']
assert len(set(ids)) == len(ids)
i = ids.index('OpenROAD.DetailedRouting')
assert ids[i+1:i+5] == [
    'Witness.RepairLateLoads', 'Witness.RerouteLateLoads',
    'Witness.RepairLateLoads-1', 'Witness.RerouteLateLoads-1',
]
print('WitnessClassic: native discovery, original steps/config/gates and late repair order PASS')
