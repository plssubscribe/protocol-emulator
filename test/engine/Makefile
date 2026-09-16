SIM ?= icarus
TOPLEVEL_LANG = verilog
ROOT := $(abspath ../..)
CORE_SOURCE ?= $(ROOT)/src/witness_core.v
VERILOG_SOURCES = $(CORE_SOURCE)
TOPLEVEL = witness_core
COCOTB_TEST_MODULES = test_engine
export PYTHONPATH := $(ROOT):$(PYTHONPATH)
COMPILE_ARGS += -g2012 -Wall
include $(shell cocotb-config --makefiles)/Makefile.sim
