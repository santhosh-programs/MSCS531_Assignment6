# Copyright (c) 2015 Jason Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" This file creates a barebones system and executes 'hello', a simple Hello
World application.
See Part 1, Chapter 2: Creating a simple configuration script in the
learning_gem5 book for more information about this script.

IMPORTANT: If you modify this file, it's likely that the Learning gem5 book
           also needs to be updated. For now, email Jason <power.jg@gmail.com>

This script uses the X86 ISA. `simple-arm.py` and `simple-riscv.py` may be
referenced as examples of scripts which utilize the ARM and RISC-V ISAs
respectively.

"""

# import the m5 (gem5) library created when gem5 is built
import m5

# import all of the SimObjects
from m5.objects import *


class CustomMinorDefaultFUPool(MinorFUPool):
    funcUnits = [
        MinorDefaultIntFU(),
        MinorDefaultIntFU(),
        MinorDefaultIntMulFU(),
        MinorDefaultIntDivFU(),
        MinorDefaultFloatSimdFU(opLat=1, issueLat=6),
        MinorDefaultPredFU(),
        MinorDefaultMemFU(),
        MinorDefaultMiscFU(),
    ]


# create the system we are going to simulate
system = System()

# Set the clock frequency of the system (and all of its children)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the system
system.mem_mode = "timing"  # Use timing accesses
system.mem_ranges = [AddrRange("512MB")]  # Create an address range
# system.multi_thread=True


# Create a simple CPU
# You can use ISA-specific CPU models for different workloads:
# `RiscvTimingSimpleCPU`, `ArmTimingSimpleCPU`.


system.cpu = X86MinorCPU(executeFuncUnits=CustomMinorDefaultFUPool())


# system.cpu.numIQEntries = 128  # Increase from default (64)
# system.cpu.numROBEntries = 256  # Increase from default (192)
# system.cpu.LQEntries = 64  # Increase from default (32)
# system.cpu.SQEntries = 64  # Increase from default (32)

# system.cpu.numPhysVecRegs=32
# system.cpu.numPhysVecPredRegs=8
# system.cpu.smtNumFetchingThreads = 1

# system.cpu.smtFetchPolicy = "RoundRobin"  # Rotate between threads
# system.cpu.smtIQPolicy = "Dynamic"  # Allow threads to dynamically share IQ
# system.cpu.smtROBPolicy = "Dynamic"  # Allow dynamic sharing of ROB
# system.cpu.smtLSQPolicy = "Partitioned"  # Dynamic sharing for LSQ
# system.cpu.smtCommitPolicy = "RoundRobin"  # Commit policy


# system.cpu.numThreads=2
# Create a memory bus, a system crossbar, in this case
system.membus = SystemXBar()

# Hook the CPU ports up to the membus
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports

# create the interrupt controller for the CPU and connect to the membus
system.cpu.createInterruptController()


# For X86 only we make sure the interrupts care connect to memory.
# Note: these are directly connected to the memory bus and are not cached.
# For other ISA you should remove the following three lines.
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# system.cpu.interrupts[1].pio = system.membus.mem_side_ports
# system.cpu.interrupts[1].int_requestor = system.membus.cpu_side_ports
# system.cpu.interrupts[1].int_responder = system.membus.mem_side_ports
# system.cpu.branchPred = TournamentBP(localPredictorSize=512, localHistoryTableSize=16384,globalPredictorSize=512, choicePredictorSize=2048,numThreads=4)
# system.cpu.smtNumFetchingThreads = 2
# system.cpu.numThreads=2

# system.cpu.commitWidth =1
# system.cpu.fetchWidth = 1
# system.cpu.renameWidth = 1
# system.cpu.issueWidth =1
# Create a DDR3 memory controller and connect it to the membus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Connect the system up to the membus
system.system_port = system.membus.cpu_side_ports

# Here we set the X86 "hello world" binary. With other ISAs you must specify
# workloads compiled to those ISAs. Other "hello world" binaries for other ISAs
# can be found in "tests/test-progs/hello".
thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(
    thispath,
    "../../../",
    "daxpy",
)

binary2 = os.path.join(
    thispath,
    "../../../",
    "tests/test-progs/hello/bin/x86/linux/hello",
)

system.workload = SEWorkload.init_compatible(binary)


# Create a process for a simple "Hello World" application
process = Process()

# process2 = Process(pid=101)
# Set the command
# cmd is a list which begins with the executable (like argv)
process.cmd = [binary]
# process2.cmd= [binary]
# Set the cpu to use the process as its workload and create thread contexts
system.cpu.workload = [process]
system.cpu.createThreads()

# set up the root SimObject and start the simulation
root = Root(full_system=False, system=system)
# instantiate all of the objects we've created above
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause()))
