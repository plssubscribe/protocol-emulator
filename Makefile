.PHONY: test unit integration model lab engine mutations synth synth-check formal synth-top-check host-mutations i2c-demo i2c-netlist

test: model unit integration engine

unit:
	@mkdir -p work
	@set -e; for divisor in 1 2 3 434; do \
	  iverilog -g2012 -Wall -s uart_tx_tb -Puart_tx_tb.DIV=$$divisor -o work/uart_tx_tb src/uart_tx.v test/uart_tx_tb.v; \
	  vvp work/uart_tx_tb; \
	done

integration:
	$(MAKE) -C test
	python -c 'import xml.etree.ElementTree as E; r=E.parse("test/results.xml"); assert not r.findall(".//failure") and not r.findall(".//error"), "simulation failed"'

model:
	python3 -m unittest discover -s test/model -v

lab: model
	python3 tools/protocol_lab.py
	python3 tools/protocol_lab.py --replay work/protocol-witness.json

engine:
	$(MAKE) -C test/engine
	python3 -c 'import xml.etree.ElementTree as E; r=E.parse("test/engine/results.xml"); assert not r.findall(".//failure") and not r.findall(".//error"), "engine simulation failed"'

mutations:
	python3 scripts/mutate-witness.py

synth:
	python3 scripts/synth-witness.py

synth-check: synth
	$(MAKE) -C test/engine CORE_SOURCE=$(abspath work/synthesis/witness_core.v) SIM_BUILD=$(abspath work/synthesis/sim_build) COCOTB_RESULTS_FILE=$(abspath work/synthesis/results.xml)
	python3 -c 'import xml.etree.ElementTree as E; r=E.parse("work/synthesis/results.xml"); assert not r.findall(".//failure") and not r.findall(".//error"), "generic netlist simulation failed"'

formal:
	python3 scripts/formal-witness.py

synth-top-check:
	python3 scripts/synth-witness.py --integrated
	I2C_SMOKE=1 $(MAKE) -C test VERILOG_SOURCES="$(abspath work/synthesis-top/tt_um_protocol_emulator.v) $(abspath test/tb.v)" SIM_BUILD=$(abspath work/synthesis-top/sim_build) COCOTB_RESULTS_FILE=$(abspath work/synthesis-top/results.xml)
	python3 -c 'import xml.etree.ElementTree as E; r=E.parse("work/synthesis-top/results.xml"); assert not r.findall(".//failure") and not r.findall(".//error"), "integrated generic netlist simulation failed"'

host-mutations:
	python3 scripts/mutate-host.py

i2c-demo:
	$(MAKE) -C test COCOTB_TEST_FILTER=i2c_stretch_sweep_and_replay

# Reuse a hash-matched generic netlist; this target does not rerun physical synthesis.
i2c-netlist:
	python3 scripts/check-integrated-netlist.py
	I2C_SMOKE=1 $(MAKE) -C test COCOTB_TEST_FILTER=i2c_stretch_sweep_and_replay VERILOG_SOURCES="$(abspath work/synthesis-top/tt_um_protocol_emulator.v) $(abspath test/tb.v)" SIM_BUILD=$(abspath work/synthesis-top/sim_build) COCOTB_RESULTS_FILE=$(abspath work/synthesis-top/i2c-results.xml)

.PHONY: spi-demo
spi-demo:
	$(MAKE) -C test COCOTB_TEST_FILTER=spi_four_modes_and_replay

.PHONY: capture-demo
capture-demo:
	$(MAKE) -C test COCOTB_TEST_FILTER="'spi_unknown_response_capture|capture_overflow_readback_and_reset'"

.PHONY: cmos5l-map cmos5l-map-check
cmos5l-map:
	python3 scripts/map-cmos5l.py

cmos5l-map-check: cmos5l-map
	$(MAKE) -C test COCOTB_TEST_FILTER="'host_load_execute_and_witness|capture_overflow_readback_and_reset|spi_unknown_response_capture'" VERILOG_SOURCES="$(abspath work/cmos5l-mapping/mapped.v) $(abspath work/cmos5l-mapping/cells.v) $(abspath test/tb.v)" SIM_BUILD=$(abspath work/cmos5l-mapping/sim_build) COCOTB_RESULTS_FILE=$(abspath work/cmos5l-mapping/results.xml)
	python3 -c 'import xml.etree.ElementTree as E; r=E.parse("work/cmos5l-mapping/results.xml"); c=[x for x in r.findall(".//testcase") if x.find("skipped") is None]; assert len(c)==3 and not r.findall(".//failure") and not r.findall(".//error")'
