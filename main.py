import asyncio
from Scale import Scale
from ClearCore import ClearCore
from dispenser import Dispenser
import scipy.signal as signal

s = Scale(716692)

m = ClearCore('192.168.1.11', 0, 6400)

d = Dispenser(m, s)

run = lambda x: asyncio.run(d.dispense(x, offset=5))

kill = lambda: asyncio.run(m.stop())
def kill():
    print(':( oops...')
    asyncio.run(m.stop())
    asyncio.run(m.disable())

def end():
    kill()
    exit()

def test(dispenser: Dispenser, n=10, w=2):
    sig = dispenser.data['weight']
    sos = signal.butter(N=n, Wn=w, output='sos')
    dispenser.data['filtered'] = signal.sosfiltfilt(sos, sig)
    dispenser.plot_data(data='filtered')
