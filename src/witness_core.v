// SPDX-License-Identifier: Apache-2.0
`default_nettype none
module witness_core (
    input wire clk, input wire rst_n,
    input wire load_valid, output wire load_ready,
    input wire [4:0] load_addr, input wire [39:0] load_word,
    input wire start, input wire abort,
    input wire [7:0] pins_in,
    output reg [7:0] pins_out, output reg [7:0] pins_oe,
    output reg running, output reg done,
    output reg [2:0] status,
    output reg [4:0] witness_pc,
    output reg [31:0] witness_cycle,
    output reg [39:0] witness_word,
    output reg [7:0] witness_observed,
    output reg [15:0] witness_samples,
    output reg [31:0] capture_data,
    output reg [5:0] capture_count,
    output reg time_wrapped
);
    reg [39:0] memory [0:31];
    reg [31:0] valid_slots;
    reg [4:0] pc;
    reg [15:0] age;
    reg [31:0] tick;
    reg [39:0] word;
    wire [3:0] opcode = word[39:36];
    wire [15:0] duration = word[31:16];
    wire [7:0] a = word[15:8];
    wire [7:0] b = word[7:0];
    function legal_word;
        input [39:0] instruction;
        reg [15:0] count;
        reg [7:0] value, mask;
        begin
            count = instruction[31:16];
            value = instruction[15:8];
            mask = instruction[7:0];
            legal_word = 1'b0;
            if (instruction[35:32] == 0) begin
                case (instruction[39:36])
                    0: legal_word = instruction[31:0] == 0;
                    1: legal_word = count != 0;
                    2: legal_word = count != 0 && mask != 0 && (value & ~mask) == 0;
                    3: legal_word = count != 0 && instruction[15:0] == 0;
                    4: legal_word = instruction[31:5] == 0;
                    5: legal_word = count != 0 && value < 8 && mask == 0;
                    default: legal_word = 1'b0;
                endcase
            end
        end
    endfunction
    wire legal = legal_word(word);
    // Look ahead to the successor so outputs can be registered without a fetch bubble.
    wire [4:0] successor = !running ? 5'b0 : opcode == 4 ? b[4:0] : pc + 5'd1;
    wire [39:0] next_word = memory[successor];
    wire next_legal = valid_slots[successor] && legal_word(next_word);
    assign load_ready = !running && rst_n && !abort;

    task enter_next;
        begin
            word <= valid_slots[successor] ? next_word : 40'b0;
            pc <= successor;
            age <= 0;
            if (next_legal && next_word[39:36] == 1) begin
                pins_out <= next_word[15:8];
                pins_oe <= next_word[7:0];
            end else begin
                if (!running) pins_out <= 0;
                if (!running || !next_legal || next_word[39:36] == 0) pins_oe <= 0;
            end
        end
    endtask

    // One terminal record per run. Its cycle is the sample index, not elapsed count.
    task terminate;
        input [2:0] reason;
        input [15:0] samples;
        begin
            running <= 1'b0;
            done <= 1'b1;
            status <= reason;
            witness_pc <= pc;
            witness_cycle <= tick;
            witness_word <= valid_slots[pc] ? word : 40'b0;
            witness_observed <= pins_in;
            witness_samples <= samples;
            pins_oe <= 0;
        end
    endtask

    always @(posedge clk) begin
        if (!rst_n) begin
            valid_slots <= 0;
            word <= 0;
            pc <= 0;
            age <= 0;
            tick <= 0;
            pins_out <= 0;
            pins_oe <= 0;
            running <= 0;
            done <= 0;
            status <= 0;
            witness_pc <= 0;
            witness_cycle <= 0;
            witness_word <= 0;
            witness_observed <= 0;
            witness_samples <= 0;
            time_wrapped <= 0;
            capture_data <= 0;
            capture_count <= 0;
        end else if (running) begin
            if (abort) begin
                terminate(3'd4, 16'd0);
            end else begin
                tick <= tick + 1'b1;
                if (&tick) time_wrapped <= 1'b1;
                if (!valid_slots[pc]) begin
                    terminate(3'd3, 16'd0);
                end else if (!legal) begin
                    terminate(3'd2, 16'd0);
                end else if (opcode == 0) begin
                    terminate(3'd0, 16'd0);
                end else if (opcode == 4) begin
                    enter_next;
                end else begin
                    if (opcode == 2 && (pins_in & b) == a) begin
                        enter_next;
                    end else if (age == duration - 1'b1) begin
                        if (opcode == 2) begin
                            terminate(3'd1, duration);
                        end else if (opcode == 5 && capture_count == 32) begin
                            terminate(3'd5, duration);
                        end else begin
                            if (opcode == 5) begin
                                capture_data <= {capture_data[30:0], pins_in[a[2:0]]};
                                capture_count <= capture_count + 1'b1;
                            end
                            enter_next;
                        end
                    end else begin
                        age <= age + 1'b1;
                    end
                end
            end
        end else if (!abort) begin
            if (load_valid) begin
                memory[load_addr] <= load_word;
                valid_slots[load_addr] <= 1'b1;
            end else if (start) begin
                running <= 1;
                done <= 0;
                status <= 0;
                enter_next;
                tick <= 0;
                witness_pc <= 0;
                witness_cycle <= 0;
                witness_word <= 0;
                witness_observed <= 0;
                witness_samples <= 0;
                time_wrapped <= 0;
                capture_data <= 0;
                capture_count <= 0;
            end
        end
    end
endmodule
`default_nettype wire
