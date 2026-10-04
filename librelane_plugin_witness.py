"""Late diode-load repair for the pinned LibreLane 3.0.0rc1 Classic flow.

Loaded by LibreLane's native plugin discovery from the project directory on both
host and container. Keep every Classic check and its configuration gates.
"""
from pathlib import Path

from librelane.flows.classic import Classic
from librelane.flows.flow import Flow
from librelane.steps import OpenROAD


class ClearSignalRoutes(OpenROAD.GlobalRouting):
    id = "Witness.ClearSignalRoutes"
    name = "Clear Obsolete Signal Routes Before Late Repair"

    def get_script_path(self):
        return str(Path(__file__).resolve().parent / "scripts/openroad/clear-signal-routes.tcl")


class RepairLateLoads(OpenROAD.RepairDesignPostGRT):
    id = "Witness.RepairLateLoads"
    name = "Repair Loads After Detailed-Route Antenna Protection"


class RerouteLateLoads(OpenROAD.DetailedRouting):
    id = "Witness.RerouteLateLoads"
    name = "Reroute After Late Load Repair"


@Flow.factory.register()
class WitnessClassic(Classic):
    # Bound the additional work to two passes. Neither convergence nor acceptance
    # is inferred from this count: extracted final metrics remain the CI gate.
    Steps = list(Classic.Steps)
    _route_index = next(
        i for i, step in enumerate(Steps) if step.id == "OpenROAD.DetailedRouting"
    )
    Steps[_route_index + 1:_route_index + 1] = [
        ClearSignalRoutes, RepairLateLoads, RerouteLateLoads,
        ClearSignalRoutes, RepairLateLoads, RerouteLateLoads,
    ]
    gating_config_vars = dict(Classic.gating_config_vars)
    gating_config_vars.update({
        "Witness.ClearSignalRoutes*": ["RUN_POST_GRT_DESIGN_REPAIR", "RUN_DRT"],
        "Witness.RepairLateLoads*": ["RUN_POST_GRT_DESIGN_REPAIR"],
        "Witness.RerouteLateLoads*": ["RUN_DRT"],
    })
