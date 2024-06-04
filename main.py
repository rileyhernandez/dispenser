import asyncio
from Scale import Scale
from ClearCore import ClearCore
from Dispenser import Dispenser


# s = Scale(716692)
# s = Scale(716710)

m = ClearCore('192.168.1.11', 0, 6400)

# d = Dispenser(m, s)

# run = lambda x: asyncio.run(d.dispense(x, offset=5))

# def kill():
#     print(':( oops...')
#     asyncio.run(m.stop())
#     asyncio.run(m.disable())

# def end():
#     kill()
#     exit()

sns = [716620, 716623, 716625, 716709]

scales = [Scale(sn) for sn in sns]

# async def test(dispenser=d):
#     while True:
#         weight = await dispenser.live_weigh()
#         print(weight)
#         await asyncio.sleep(0.5)

#      self.cells = [VoltageRatioInput() for _ in range(4)]
#         for cell in range(len(self.cells)):
#             self.cells[cell].setDeviceSerialNumber(SIN)
#             self.cells[cell].setChannel(cell)
#             self.cells[cell].openWaitForAttachment(2000)
#             self.cells[cell].setDataInterval(self.cells[cell].getMinDataInterval())