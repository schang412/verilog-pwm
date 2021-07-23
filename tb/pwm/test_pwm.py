
import itertools
import logging
import os
import sys

import configparser

import cocotb_test.simulator
import pytest

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.regression import TestFactory

class TB(object):
    def __init__(self, dut, clk_ns=10):
        self.dut = dut

        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        self.clk_ns = clk_ns

        cocotb.fork(Clock(dut.clk, clk_ns, units="ns").start())

    async def set_duty(self, duty):
        self.dut.compare <= int(duty * (2 ** int(os.environ["PARAM_DATA_WIDTH"]) - 1))

    async def reset(self):
        self.dut.rst.setimmediatevalue(0)
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst <= 1
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst <= 0
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)



async def run_test(dut, duty_cycle=None, prescale=None):
    tb = TB(dut)
    await tb.reset()

    # assign the prescale
    dut.prescale <= prescale

    # write the duty cycle
    await tb.set_duty(duty_cycle)

    # enable the module
    dut.en.setimmediatevalue(1)

    # wait for the first rising edge on the output since the first edge can be delayed
    # due to the previous state
    await RisingEdge(dut.out)

    # measure the duty and period of the pwm output
    measured_duties  = []
    measured_periods = []
    for i in range(5):
        await RisingEdge(dut.out)
        tr0 = cocotb.utils.get_sim_time(units="ns")
        await FallingEdge(dut.out)
        tf0 = cocotb.utils.get_sim_time(units="ns")
        await RisingEdge(dut.out)
        tr1 = cocotb.utils.get_sim_time(units="ns")

        measured_duties.append((tf0 - tr0)/(tr1 - tr0))
        measured_periods.append(tr1 - tr0)

    measured_duty   = sum(measured_duties)  / len(measured_duties)
    measured_period = sum(measured_periods) / len(measured_periods)

    assert measured_duty == pytest.approx(duty_cycle, 0.1)

    # the period is determined by the clock period
    # the prescale is divided by 2, since we only update on posedge clk
    # then we need to multiply by the data width
    assert measured_period == pytest.approx(tb.clk_ns * (prescale/2) * 2 ** (int(os.environ["PARAM_DATA_WIDTH"])), 0.01)

    dut.en.setimmediatevalue(0)

    await Timer(1, units="us")
    await RisingEdge(dut.clk)

if cocotb.SIM_NAME:
    factory = TestFactory(run_test)
    factory.add_option("duty_cycle", [0.5, 0.2, 0.8])
    factory.add_option("prescale", [2, 4, 10])
    factory.generate_tests()


tests_dir = os.path.dirname(__file__)
rtl_dir = os.path.abspath(os.path.join(tests_dir, '../../rtl'))

def test_pwm(request):
    dut = "pwm"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut

    verilog_files = [
        f"{dut}.sv"
    ]
    verilog_sources = [os.path.join(rtl_dir, x) for x in verilog_files]

    # read the default parameters
    config = configparser.ConfigParser()
    config.read(os.path.join(tests_dir,"../parameters.ini"))
    parameters = config._sections['default']

    extra_env = {f'PARAM_{k.upper()}': str(v) for k, v in parameters.items()}

    sim_build = os.path.join(tests_dir, "sim_build",
        request.node.name.replace('[', '-').replace(']', ''))

    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        extra_env=extra_env,
    )


