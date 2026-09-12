# Working on this project

Read README.md, docs/roadmap.md and accepted docs/decisions/*.md first.
Teach through runnable milestones; explain concepts when needed to unblock the change.
Document consequential architecture choices in a new numbered ADR and update the roadmap.
Keep synthesizable Verilog in src/ and list each source in info.yaml and test/Makefile.
Preserve the Tiny Tapeout port interface and safe unused outputs.
Run make test for RTL changes. Record which physical checks actually ran; never equate
RTL success with timing closure or tapeout readiness. Do not silently change the PDK,
clock target, pin map, reset semantics or instruction timing.
