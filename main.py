import asyncio
from Scale import Scale
from ClearCore import ClearCore
from dispenser import Dispenser


s = Scale(716692)
# s = Scale(716710)

m = ClearCore('192.168.1.11', 0, 6400)

d = Dispenser(m, s)

run = lambda x: asyncio.run(d.dispense(x, offset=5))

def kill():
    print(':( oops...')
    asyncio.run(m.stop())
    asyncio.run(m.disable())

def end():
    kill()
    exit()

async def test(dispenser=d):
    while True:
        weight = await dispenser.live_weigh()
        print(weight)
        await asyncio.sleep(0.5)