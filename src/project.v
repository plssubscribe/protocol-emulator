// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
`default_nettype none
module tt_um_protocol_emulator (
    input wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input wire ena,
    input wire clk,
    input wire rst_n
);
    wire tx;
    wire ready;
    // 50 MHz / 434 = 115207.37 baud (+0.0064% vs 115200).
    uart_tx #(.CLKS_PER_BIT(434)) transmitter (
        .clk(clk), .rst_n(rst_n), .valid(1'b1), .data(8'h55),
        .ready(ready), .tx(tx)
    );
    wire unlocked, host_error, running, done, time_wrapped;
    wire load_valid, load_ready, start, abort;
    wire [4:0] load_addr, witness_pc;
    wire [39:0] load_word, witness_word;
    wire [31:0] witness_cycle, capture_data;
    wire [5:0] capture_count;
    wire [15:0] witness_samples;
    wire [7:0] witness_observed, protocol_out, protocol_oe;
    wire [2:0] status;
    wire miso;
    reg [7:0] input_meta, input_sync;
    always @(posedge clk) begin
        if (!rst_n) begin
            input_meta <= 0;
            input_sync <= 0;
        end else begin
            input_meta <= uio_in;
            input_sync <= input_meta;
        end
    end
    witness_core engine (
        .clk(clk), .rst_n(rst_n), .load_valid(load_valid), .load_ready(load_ready),
        .load_addr(load_addr), .load_word(load_word), .start(start), .abort(abort),
        .pins_in(input_sync), .pins_out(protocol_out), .pins_oe(protocol_oe),
        .running(running), .done(done), .status(status), .witness_pc(witness_pc),
        .witness_cycle(witness_cycle), .witness_word(witness_word),
        .witness_observed(witness_observed), .witness_samples(witness_samples),
        .time_wrapped(time_wrapped), .capture_data(capture_data), .capture_count(capture_count)
    );
    witness_host_spi host (
        .clk(clk), .rst_n(rst_n), .sclk_in(ui_in[0]), .mosi_in(ui_in[1]),
        .cs_n_in(ui_in[2]), .miso(miso), .unlocked(unlocked), .host_error(host_error),
        .load_valid(load_valid), .load_ready(load_ready), .load_addr(load_addr),
        .load_word(load_word), .start(start), .abort(abort), .running(running),
        .done(done), .time_wrapped(time_wrapped), .status(status),
        .witness_pc(witness_pc), .witness_cycle(witness_cycle),
        .witness_word(witness_word), .witness_observed(witness_observed),
        .witness_samples(witness_samples), .capture_data(capture_data), .capture_count(capture_count)
    );
    assign uo_out = {3'b0, unlocked && host_error, unlocked && done,
                     unlocked && running, miso, tx};
    assign uio_out = unlocked ? protocol_out : 8'b0;
    assign uio_oe = unlocked ? protocol_oe : 8'b0;
    // ena remains the TT selection indication, not an application clock-enable.
    wire _unused = &{ui_in[7:3], ena, ready, 1'b0};
endmodule
