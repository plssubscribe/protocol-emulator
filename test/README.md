# UART verification

From the repository root, activate `.venv` and run `make test`.
`make unit` uses Icarus alone; `make integration` also needs cocotb.
The pin-level test writes `test/tb.fst` and `test/results.xml`.
See `../docs/verification.md` for coverage and remaining physical checks.

For the inherited gate simulation workflow, the GDS action supplies
`gate_level_netlist.v` and the CMOS5L PDK; it then runs `make GATES=yes` here.
