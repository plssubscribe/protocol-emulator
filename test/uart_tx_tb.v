`timescale 1ns/1ps
`default_nettype none
module uart_tx_tb;
    parameter integer DIV = 3;
    reg clk = 0;
    reg rst_n = 0;
    reg valid = 0;
    reg [7:0] data = 0;
    wire ready, tx;
    uart_tx #(.CLKS_PER_BIT(DIV)) dut(clk, rst_n, valid, data, ready, tx);
    task tick;
        begin clk = 0; #5; clk = 1; #5; end
    endtask
    integer value, bit_idx, cycle;
    reg [9:0] expected;
    initial begin
        tick;
        if (tx !== 1 || ready !== 1) $fatal(1, "reset");
        rst_n = 1;
        repeat (3) begin
            tick;
            if (tx !== 1 || ready !== 1) $fatal(1, "idle");
        end
        for (value = 0; value < 256; value = value + 1) begin
            data = value;
            expected = {1'b1, data, 1'b0};
            valid = 1;
            tick;
            for (bit_idx = 0; bit_idx < 10; bit_idx = bit_idx + 1) begin
                for (cycle = 0; cycle < DIV; cycle = cycle + 1) begin
                    if (tx !== expected[bit_idx] || ready !== 0)
                        $fatal(1, "frame value=%d bit=%d cycle=%d", value, bit_idx, cycle);
                    // Requests while busy must not corrupt the latched frame.
                    data = ~value;
                    tick;
                end
            end
            if (tx !== 1 || ready !== 1) $fatal(1, "completion");
            valid = 0;
            tick;
        end
        $display("PASS: all 256 bytes, DIV=%0d", DIV);
        $finish;
    end
endmodule
