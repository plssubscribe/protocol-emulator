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
    assign uo_out = {7'b0, tx};
    assign uio_out = 8'b0;
    assign uio_oe = 8'b0;
    // ena is the TT selection indication, not a user clock-enable.
    wire _unused = &{ui_in, uio_in, ena, ready, 1'b0};
endmodule
