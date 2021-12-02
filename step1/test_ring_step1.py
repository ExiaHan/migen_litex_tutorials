#!/usr/bin/env python3

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from platform_tango import *

# CRG ----------------------------------------------------------------------------------------------

class CRG(Module):
    def __init__(self, platform):
        self.rst = Signal()
        self.clock_domains.cd_sys   = ClockDomain()

        # # #

        clk = platform.request("sys_clk")
        rst_n = platform.request("user_btn", 0)

        self.comb += self.cd_sys.clk.eq(clk)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~rst_n)

        platform.add_period_constraint(clk, 1e9/24e6)

# Design -------------------------------------------------------------------------------------------

class Tuto(Module):
    def __init__(self, platform):

        crg = CRG(platform)
        self.submodules += crg

        led = platform.request("user_led", 1)
        blink = Blink(24)
        self.submodules += blink
        self.comb += led.eq(blink.out)

        data = platform.request("do")
        ring = RingSerialCtrl()
        self.submodules += ring
        self.comb += data.eq(~ring.do)

# Blinker -------------------------------------------------------------------------------------------

class Blink(Module):
    def __init__(self, bit):
        self.out = Signal()

        ###

        counter = Signal(25)
        self.comb += self.out.eq(counter[bit])
        self.sync += counter.eq(counter + 1)

# RingSerialCtrl -------------------------------------------------------------------------------------------

#                ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐
#                │DI  DO│   │DI  DO│   │DI  DO│   │DI  DO│   │DI  DO│     Next leds
#        FPGA ───►      ├───►      ├───►      ├───►      ├───►      ├───►     or
#                │ LED0 │   │ LED1 │   │ LED2 │   │ LED3 │   │ LED4 │   end of chain.
#                └──────┘   └──────┘   └──────┘   └──────┘   └──────┘
#                 24-bit     24-bit     24-bit     24-bit     24-bit
#
#    WS2812/NeoPixel Leds are smart RGB Leds controlled over a simple one wire protocol:
#     - Each Led will "digest" a 24-bit control word:  (MSB) G-R-B (LSB).
#     - Leds can be chained through DIN->DOUT connection.
#
#     Each control sequence is separated by a reset code: Line low for > 50us.
#     Zeros are transmitted as:
#                       ┌─────┐
#                       │ T0H │           │  T0H = 400ns +-150ns
#                       │     │    T0L    │  T0L = 800ns +-150ns
#                             └───────────┘
#     Ones are transmitted as:
#                       ┌──────────┐
#                       │   T1H    │      │  T1H = 850ns +-150ns
#                       │          │ T1L  │  T1L = 450ns +-150ns
#                                  └──────┘

# You have to send 24 pulses like this:
#
#                       ┌──────────┐
#                       │   T1H    │      │  T1H = 850ns
#                       │          │ T1L  │  T1L = 450ns
#                                  └──────┘
#
#
# You can send 24 pulses every 'period' of time
#
# Note: 850ns is 19 clock cycles @24MHz
#       450ns is 10 clock cycles @24MHz

class RingSerialCtrl(Module):
    def __init__(self):
        self.do = Signal()

        ###

        # Add your internal signals here
        # If you want a signal that can hold a maximum value of my_value
        # t_high_cnt = Signal(max=my_value)
        # Signals are always initialized to '0' unless you explicitely
        # assign a reset value:
        # az = Signal(8, reset=0x25)

        # Assign a value to a signal is done with .eq
        # my_signal.eq(1)

        self.sync += [
            If( #condition,
                # statement1,
                # statement2,
                # ...
            ).Else(
                # statement3,
                 # statement4,
                 # ...
            ),
            # statement5,
        ]

        # You can as much as self.sync as you want
        # it can improve code readability
        self.sync += [
            # statement6,
        ]

# Test -------------------------------------------------------------------------------------------

def test():
    loop = 0
    while (loop < 10000):
        yield
        loop = loop + 1

# Build --------------------------------------------------------------------------------------------

def main():

    build_dir= 'gateware'
    platform= Platform()

    if "load" in sys.argv[1: ]:
        prog= platform.create_programmer()
        prog.load_bitstream(os.path.join(
            build_dir, "impl", "pnr", "project.fs"))
        exit()

    if "flash" in sys.argv[1: ]:
        prog= platform.create_programmer()
        prog.flash(0, os.path.join(build_dir, "impl", "pnr", "project.fs"))
        exit()

    if "sim" in sys.argv[1: ]:
        ring = RingSerialCtrl()
        run_simulation(ring, test(), clocks={"sys": 1e9/24e6}, vcd_name="sim.vcd")
        exit()

    design = Tuto(platform)
    platform.build(design, build_dir=build_dir)

if __name__ == "__main__":
    main()