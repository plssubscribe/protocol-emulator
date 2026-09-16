// SPDX-License-Identifier: Apache-2.0
// Public-interface safety properties, under one initial synchronous reset edge.
module witness_safety (
    input wire clk, rst_n, load_valid, start, abort,
    input wire [4:0] load_addr,
    input wire [39:0] load_word,
    input wire [7:0] pins_in
);
    wire load_ready, running, done, time_wrapped;
    wire [7:0] pins_out, pins_oe, witness_observed;
    wire [2:0] status;
    wire [4:0] witness_pc;
    wire [31:0] witness_cycle, capture_data;
    wire [5:0] capture_count;
    wire [39:0] witness_word;
    wire [15:0] witness_samples;
    witness_core dut (.*);
    reg past_valid = 0;
    wire [105:0] record = {status, witness_pc, witness_cycle, witness_word,
                          witness_observed, witness_samples, time_wrapped, done};
    always @(posedge clk) begin
        past_valid <= 1;
        if (!past_valid) assume(!rst_n);
        if (past_valid) begin
            assert(capture_count <= 32);
            assert(running || pins_oe == 0);
            assert(!done || !running);
            if (!$past(rst_n)) begin
                assert(!running && !done && pins_oe == 0 && pins_out == 0);
                assert(capture_count == 0 && capture_data == 0);
            end
            if ($past(rst_n && running && abort)) begin
                assert(!running && done && status == 4 && pins_oe == 0);
                assert(capture_count == $past(capture_count) && capture_data == $past(capture_data));
            end
            if ($past(rst_n && done && (!start || load_valid || abort))) begin
                assert(record == $past(record));
                assert(capture_count == $past(capture_count) && capture_data == $past(capture_data));
            end
            if ($past(rst_n && !running && !abort && load_valid)) begin
                assert(!running);
            end
        end
    end
endmodule
