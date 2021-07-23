# Verilog PWM

[![Regression Tests](https://github.com/schang412/verilog-pwm/actions/workflows/regression-test.yml/badge.svg)](https://github.com/schang412/verilog-pwm/actions/workflows/regression-test.yml)

GitHub repository: https://github.com/schang412/verilog-pwm

## Documentation

The main code for the core exists in the `rtl` subdirectory. There are two implementations of the module, one without a window, and one with.

The modules take a parameter `DATA_WIDTH` which determines the width of the compare register and consequently affects the PWM frequency. The modules also include a `prescale` input signal which can be used to dynamically adjust the frequency. The `prescale` input must be even number of at least 2.


### Window

For the PWM module with the window signal, an additional parameter `PADDING` is offered. The window signal goes high when the PWM output has been high for `PADDING` time and will stay high for `PADDING` time. If 2\*`PADDING` is wider than the high level output pulse, the window signal will stay low.

```
              _______        _______        _______
      out: __|       |______|       |______|       |______
                ___            ___            ___
   window: ____|   |__________|   |__________|   |________

```

I use the window signal to sample the back EMF of a brushless motor only when power is being supplied to the motor.

### Calculations
```
PWM_DUTY      = {compare} / (2^{DATA_WIDTH} - 1)
PWM_PERIOD    = {CLK_PERIOD_NS} * {prescale}/2 * 2^{DATA_WIDTH}
PWM_PADDING_L = {CLK_PERIOD_NS} * {prescale}/2 * {PADDING}
```


### Source Files
```
rtl/pwm.sv          : Verilog PWM module
rtl/pwm_window.sv   : Verilog PWM module with a window signal.
```

## Testing
Running the included testbenches requires [cocotb](https://github.com/cocotb/cocotb) and [Icarus Verilog](http://iverilog.icarus.com/). The testbenches can be run with pytest directly (requires [cocotb-test](https://github.com/themperek/cocotb-test)), pytest via tox, or via cocotb makefiles. This code requires at least iverilog v11.0 because of the SystemVerilog constructs.
