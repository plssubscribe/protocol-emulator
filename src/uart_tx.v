// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
`default_nettype none
// 8N1 UART. Accepts valid/data only when ready is high at a rising edge.
// CLKS_PER_BIT must be >= 1. Reset is synchronous, active low.
module uart_tx #(
    parameter integer CLKS_PER_BIT = 434
) (
    input wire clk,
    input wire rst_n,
    input wire valid,
    input wire [7:0] data,
    output wire ready,
    output wire tx
);
    localparam integer COUNT_WIDTH = (CLKS_PER_BIT <= 1) ? 1 : $clog2(CLKS_PER_BIT);
    localparam [COUNT_WIDTH-1:0] RELOAD = CLKS_PER_BIT - 1;
    reg [COUNT_WIDTH-1:0] count;
    reg [9:0] frame;
    reg [3:0] bits_left;
    assign ready = (bits_left == 0);
    assign tx = ready ? 1'b1 : frame[0];

    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 0;
            frame <= 10'h3ff;
            bits_left <= 0;
        end else if (ready) begin
            if (valid) begin
                frame <= {1'b1, data, 1'b0};
                bits_left <= 10;
                count <= RELOAD;
            end
        end else if (count != 0) begin
            count <= count - 1'b1;
        end else begin
            frame <= {1'b1, frame[9:1]};
            bits_left <= bits_left - 1'b1;
            count <= RELOAD;
        end
    end
endmodule
