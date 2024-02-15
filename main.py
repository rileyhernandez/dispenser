import asyncio
import numpy as np
import matplotlib.pyplot as plt
from STF06_IP import STF
from load_cell import LoadCell
from dispenser import Dispenser

a = lambda f, x: asyncio.run(f(x))

# motor = STF('192.168.1.10', 200, 2)
# asyncio.run(motor.set_power(1))

print('Running...')
# d = Dispenser(motor, [LoadCell(i) for i in range(4)])

d = Dispenser('filler', [LoadCell(i) for i in range(4)])
# asyncio.run(d.tare())

asyncio.run(d.test_avg(t=10))
d.plot_data()
