// SPDX-License-Identifier: Apache-2.0
`default_nettype none
module witness_host_spi (
    input wire clk, rst_n,
    input wire sclk_in, mosi_in, cs_n_in,
    output wire miso,
    output reg unlocked, output reg host_error,
    output reg load_valid, output reg [4:0] load_addr,
    output reg [39:0] load_word,
    input wire load_ready,
    output reg start, output reg abort,
    input wire running, done, time_wrapped,
    input wire [2:0] status,
    input wire [4:0] witness_pc,
    input wire [31:0] witness_cycle,
    input wire [39:0] witness_word,
    input wire [7:0] witness_observed,
    input wire [15:0] witness_samples,
    input wire [31:0] capture_data,
    input wire [5:0] capture_count
);
    reg [1:0] clock_sync, data_sync, select_sync;
    reg clock_prev, select_prev;
    reg [63:0] rx, tx, reply;
    reg [6:0] count;
    reg [7:0] crc;
    reg [39:0] snapshot1, snapshot2, snapshot3;
    wire [7:0] command = rx[55:48];
    wire [39:0] payload = rx[47:8];
    wire [39:0] page0 = {unlocked, host_error, time_wrapped, running, done,
                         status, witness_cycle};
    wire [39:0] page1 = {3'b0, witness_pc, witness_observed, witness_samples, 8'b0};
    wire select_fall = select_prev && !select_sync[1];
    wire select_rise = !select_prev && select_sync[1];
    wire clock_rise = !clock_prev && clock_sync[1];
    wire clock_fall = clock_prev && !clock_sync[1];

    function [7:0] crc_bit;
        input [7:0] old_crc;
        input bit_in;
        begin
            crc_bit = {old_crc[6:0], 1'b0} ^ ((old_crc[7] ^ bit_in) ? 8'h07 : 8'h00);
        end
    endfunction
    function [63:0] response;
        input [7:0] code;
        input [39:0] data;
        reg [55:0] body;
        reg [7:0] sum;
        integer bit_index;
        begin
            body = {8'h5a, code, data};
            sum = 0;
            for (bit_index = 55; bit_index >= 0; bit_index = bit_index - 1)
                sum = crc_bit(sum, body[bit_index]);
            response = {body, sum};
        end
    endfunction
    task reject;
        input [7:0] code;
        begin
            reply <= response(code, 40'b0);
            if (unlocked) host_error <= 1;
        end
    endtask
    assign miso = unlocked && !select_sync[1] ? tx[63] : 1'b0;

    always @(posedge clk) begin
        if (!rst_n) begin
            clock_sync <= 0;
            data_sync <= 0;
            select_sync <= 2'b11;
            clock_prev <= 0;
            select_prev <= 1;
            rx <= 0;
            tx <= 0;
            reply <= 0;
            count <= 0;
            crc <= 0;
            unlocked <= 0;
            host_error <= 0;
            load_valid <= 0;
            load_addr <= 0;
            load_word <= 0;
            start <= 0;
            abort <= 0;
            snapshot1 <= 0;
            snapshot2 <= 0;
            snapshot3 <= 0;
        end else begin
            clock_sync <= {clock_sync[0], sclk_in};
            data_sync <= {data_sync[0], mosi_in};
            select_sync <= {select_sync[0], cs_n_in};
            clock_prev <= clock_sync[1];
            select_prev <= select_sync[1];
            load_valid <= 0;
            start <= 0;
            abort <= 0;
            if (select_fall) begin
                count <= 0;
                crc <= 0;
                rx <= 0;
                tx <= reply;
            end else if (select_rise) begin
                if (count != 64) begin
                    reject(8'd2);
                end else if (rx[63:56] != 8'ha7 || rx[7:0] != crc) begin
                    reject(8'd1);
                end else if (command == 8'h01 && payload == 40'h5749544e53) begin
                    unlocked <= 1;
                    reply <= response(0, 40'd1);
                end else if (!unlocked) begin
                    reject(8'd4);
                end else if (command[7:5] == 3'b001) begin
                    if (!load_ready) reject(8'd3);
                    else begin
                        load_valid <= 1;
                        load_addr <= command[4:0];
                        load_word <= payload;
                        reply <= response(0, 0);
                    end
                end else if (payload != 0) begin
                    reject(8'd4);
                end else begin
                    case (command)
                        8'h00: reply <= response(0, 40'd1);
                        8'h40: begin
                            if (running) reject(8'd3);
                            else begin
                                start <= 1;
                                reply <= response(0, 0);
                            end
                        end
                        8'h60: begin
                            abort <= 1;
                            reply <= response(0, 0);
                        end
                        8'h80: begin
                            snapshot1 <= page1;
                            snapshot2 <= witness_word;
                            snapshot3 <= {2'b0, capture_count, capture_data};
                            reply <= response(0, page0);
                        end
                        8'h81: reply <= response(0, snapshot1);
                        8'h82: reply <= response(0, snapshot2);
                        8'h83: reply <= response(0, snapshot3);
                        default: reject(8'd4);
                    endcase
                end
            end else if (!select_sync[1]) begin
                if (clock_rise) begin
                    if (count < 64) begin
                        rx <= {rx[62:0], data_sync[1]};
                        if (count < 56) crc <= crc_bit(crc, data_sync[1]);
                    end
                    if (count < 65) count <= count + 1'b1;
                end
                if (clock_fall && count != 0) tx <= {tx[62:0], 1'b0};
            end
        end
    end
endmodule
`default_nettype wire
