import m5
from m5.objects import *


class L1Cache(Cache):
    """Simple L1 Cache with default values"""

    assoc = 8
    tag_latency = 1
    data_latency = 1
    response_latency = 1
    mshrs = 16
    tgts_per_mshr = 20

    def connectBus(self, bus):
        """Connect this cache to a memory-side bus"""
        self.mem_side = bus.cpu_side_ports

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU-side port
        This must be defined in a subclass"""
        raise NotImplementedError


class L1ICache(L1Cache):
    """Simple L1 instruction cache with default values"""

    # Set the default size
    # size = "32kB"

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU icache port"""
        self.cpu_side = cpu.icache_port


class L1DCache(L1Cache):
    """Simple L1 data cache with default values"""

    # Set the default size
    # size = "32kB"

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU dcache port"""
        self.cpu_side = cpu.dcache_port


class L2Cache(Cache):
    """Simple L2 Cache with default values"""

    # Default parameters
    # size = "512kB"
    assoc = 16
    tag_latency = 10
    data_latency = 10
    response_latency = 1
    mshrs = 20
    tgts_per_mshr = 12

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports


# System Parameters
num_cores = 4  # Number of CPU cores
vector_size = 1024  # Size of the input vectors

# Create the system
system = System()

# Set the clock and voltage domain
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the memory system
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')]

# Create
# system.cpu = []
# for i in range(num_cores):
#     cpu = X86MinorCPU()  # Use X86MinorCPU
#     cpu.createThreads()
#     cpu.clk_domain = SrcClockDomain()
#     cpu.clk_domain.clock = '2GHz'
#     system.cpu.append(cpu)  # Add CPU to the system

# Create the L1 caches
system.cpu = [X86MinorCPU(cpu_id=i, clk_domain=SrcClockDomain(
    clock='2GHz', voltage_domain=VoltageDomain())) for i in range(num_cores)]
for cpu in system.cpu:
    print('single')
    cpu.l1d = L1DCache(size='64KiB', assoc=2)
    cpu.l1i = L1ICache(size='32KiB', assoc=2)
    cpu.l2 = L2Cache(size='256KiB', assoc=8)
    cpu.l1d.connectCPU(cpu)  # L1 Data cache connected to CPU's dcache port
    cpu.l1i.connectCPU(cpu)
    # Connect the caches

    # cpu.l2.connectCPUSideBus(cpu.l1d)

# Create a bus for the CPUs and connect it to the L2 caches
# system.l2bus = [L2XBar(width=32) for i in range(num_cores)]
# system.iobus = IOXBar()
system.membus = [SystemXBar() for i in range(num_cores+1)]

for i in range(num_cores):
    cpu = system.cpu[i]
    cpu.createThreads()
    cpu.createInterruptController()
    cpu.l1d.connectBus(system.membus[i])
    cpu.l1i.connectBus(system.membus[i])
    # cpu.l2.connectMemSideBus(system.membus)
    cpu.l2.connectCPUSideBus(system.membus[i])
    cpu.l2.connectMemSideBus(system.membus[i])

    cpu.interrupts[0].int_requestor = system.membus[4].cpu_side_ports
    cpu.interrupts[0].int_responder = system.membus[4].mem_side_ports
    cpu.interrupts[0].pio = system.membus[4].mem_side_ports
    # system.l2bus[i].mem_side_ports = system.membus.cpu_side_ports
    # cpu.icache_port = system.l2bus.cpu_side_ports
    # cpu.dcache_port = system.l2bus.cpu_side_ports
# Create a system-wide bus and connect the L2 bus to it


# Create the memory controller and connect it to the membus
# system.mem_ctrl = DDR3_1600_8x8()
# system.mem_ctrl.range = system.mem_ranges[0]

system.mem_ctrl = MemCtrl(dram=DDR3_1600_8x8())
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus[4].mem_side_ports

# system.mem_ctrl.dram = system.membus.mem_side_ports

thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(thispath, "../../../", "daxpy")
# Create the process and set the command
process = Process()
# Assuming you have a compiled ARM binary named 'daxpy.arm'
process.cmd = [binary]

# Set the process for each CPU core
for cpu in system.cpu:
    cpu.workload = process
system.workload = SEWorkload.init_compatible(binary)
# Create the system port and connect it to the membus
system.system_port = system.membus[0].cpu_side_ports

# Set up the root and instantiate the simulation
root = Root(full_system=False, system=system)
m5.instantiate()

# Run the simulation
print("Beginning simulation!")
exit_event = m5.simulate()

# Print simulation statistics
print('Exiting @ tick {} because {}'.format(m5.curTick(), exit_event.getCause()))
