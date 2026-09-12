.PHONY: test unit integration

test: unit integration

unit:
	@mkdir -p work
	@set -e; for divisor in 1 2 3 434; do \
	  iverilog -g2012 -Wall -s uart_tx_tb -Puart_tx_tb.DIV=$$divisor -o work/uart_tx_tb src/uart_tx.v test/uart_tx_tb.v; \
	  vvp work/uart_tx_tb; \
	done

integration:
	$(MAKE) -C test
	python -c 'import xml.etree.ElementTree as E; r=E.parse("test/results.xml"); assert not r.findall(".//failure") and not r.findall(".//error"), "simulation failed"'
