`timescale 1ns / 1ps

/*
 * Module `pwm_window`
 * This module generates a PWM signal from the contents in the compare register.
 *
 * The duty cycle of the output waveform can be calculated as `{compare} / ((2^{DATA_WIDTH} - 1)`
 * The period of the output waveform can be calculated as `{CLK_PER_NS} * ({prescale}/2) * (2^{DATA_WIDTH})`
 * The padding count can be converted to time by `{CLK_PER_NS} * ({prescale}/2) * {PADDING}`
 *
 * Parameters:
 *      DATA_WIDTH: the width of the compare and prescale inputs
 *      PADDING: the count to pad the output with to generate the window
 *
 * Inputs:
 *      prescale: a number to divide the clock by (must be an even number)
 *      compare: a number that sets the duty cycle of the pwm output
 *
 * Outputs:
 *      out: the pwm output signal
 *      window: provides a logic high output when out has been high for PADDING counts, and will stay high for PADDING counts
 *
 * Waveform:
 *              _______        _______        _______
 *      out: __|       |______|       |______|       |______
 *                ___            ___            ___
 *   window: ____|   |__________|   |__________|   |________
 */

module pwm_window #(
    parameter DATA_WIDTH = 8,
    parameter PADDING = 30
)
(
    input  wire clk,
    input  wire rst,

    input  wire en,

    input  wire [DATA_WIDTH-1:0] prescale,
    input  wire [DATA_WIDTH-1:0] compare,

    output wire window,
    output wire out
);

reg [DATA_WIDTH-1:0] prescale_counter_reg = 0;
reg [DATA_WIDTH-1:0] int_pwm_counter_reg  = 0;
reg [DATA_WIDTH-1:0] int_compare_reg      = 0;

enum reg {LOW, HIGH} pwm_state = LOW;
reg window_state = LOW;

assign out = (pwm_state == HIGH);
assign window = (window_state == HIGH);

always_ff @(posedge clk) begin : proc_pwm_window
    if (rst | !en) begin
        prescale_counter_reg <= 0;
        int_pwm_counter_reg <= 0;
        pwm_state <= LOW;
    end else begin

        prescale_counter_reg <= prescale_counter_reg + 1;
        if (prescale_counter_reg == (prescale >> 1)) begin
            prescale_counter_reg <= 1;

            // assume the state is high, and set it low if it exceeds the compare register
            pwm_state <= HIGH;
            int_pwm_counter_reg <= int_pwm_counter_reg + 1;
            if (int_pwm_counter_reg > int_compare_reg) begin
                pwm_state <= LOW;
            end

            // assume the window is low, then set high when condition met
            window_state <= LOW;
            if ((int_pwm_counter_reg >= PADDING) && (int_pwm_counter_reg <= int_compare_reg - PADDING) && (int_compare_reg > PADDING*2)) begin
                window_state <= HIGH;
            end

            // only latch the compare when the pwm counter overflows
            if (int_pwm_counter_reg == 0) begin
                int_compare_reg <= compare;
            end
        end
    end
end

endmodule : pwm_window