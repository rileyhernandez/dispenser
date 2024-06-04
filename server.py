from typing import List, Awaitable
from dataclasses import dataclass
from Dispenser import Dispenser
from Scale import Scale
from ClearCore import ClearCore
import asyncio
import socket

HEADER = '\x02'
CR = '\x13'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = '127.0.0.1'
PORT = 8888
s.bind((HOST, PORT))
s.listen(1)
print("Waiting for a connection...")
connection, address = s.accept()
print(f'Connected to {address}')
buffer_size = 1024
message = connection.recv(buffer_size)

scale = Scale(716692)
motor = ClearCore('192.168.1.11', 0, 6400)
dispenser = Dispenser(motor, scale)

@dataclass
class Event:
    task: Awaitable | None = None
    response: str | None = None
    queue: List[Awaitable] = []

event = Event()

async def main():
    asyncio.gather(server(), execute())

async def server():
    while True:
        status = await connection.recv(buffer_size)
        if status != None:
            event.task = status
        if event.response != None:
            connection.sendall(event.response.encode())
            event.response = None

async def execute():
    while True:
        if event.task != None:
            response = await event.task()
            event.task = None
            event.response = response

async def read(msg: str) -> Awaitable:
        """Takes an incoming message and returns the encoded message.
        """
        try:
            assert msg[0] == HEADER
            assert msg[-1] == CR
            dispenser_id = msg[1:3]
            command = msg[3:5]
            amount = msg[5:-1]
        except:
            raise Exception('Invalid Command')
        match command:
            case 'DS':
                task = asyncio.create_task(dispense(serving=amount))
            case 'CA':
                task = asyncio.create_task(calibrate(test_mass=amount))
            case 'WE':
                task = asyncio.create_task(weigh())
            case 'TR':
                task = asyncio.create_task(tare())
            case 'CL':
                task = asyncio.create_task(clear())
            case 'ST':
                task = asyncio.create_task(stop())
            case None:
                task = None
        return task

async def dispense(serving: float) -> str:
    """Dispenses a given amount from a given dispenser.
    """
    await dispenser.dispense(serving=serving)
    return 'Success/status message'
        
async def calibrate(test_mass: float) -> str:
    """Calibrates a given dispenser with a given test mass.
    """
    await dispenser.calibrate(test_mass=test_mass)
    return 'Success/status message'

async def weigh() -> str:
    """Measures the weight on a given dispenser.
    """
    await dispenser.weigh()
    return 'Success/status message'

async def tare() -> str:
    """Tares a given dispenser.
    """
    await dispenser.tare()
    return 'Success/status message'

async def clear() -> str:
    """Clears out the ingredient from a given dispenser.
    """
    await dispenser.clear()
    return 'Success/status message'

async def stop() -> str:
    """Stops whatever task is being actively executed.
    """
    return

















# async def execute(event):
#     while True:
#         await event.wait()
#         do_task()

# async def receive_task():
#     while True:
#         await check

# async def server():
#     while True:
#         await get_process_status()
#         if

# async def execute_task():
#     while True:
#         if Event.task != None


















HEADER = '\x02'
CR = '\x13'

class Event:
    def __init__(self, dispensers:Dict[str, Dispenser]):
        self.dispensers = dispensers # dictionary of dispensers with key='D0'
        self.task: None | Awaitable = None

    async def main(self):
        asyncio.gather(self.check_status, self.execute_task)

    async def run(self):
        """Waits for a message; once one is received it coruns receive() and read().
        If another message is received, it is placed in the queue by its priority.
        """
        if self.task:
            asyncio.gather(self.receive(), self.task())
        else:
            self.task = await self.receive()

    async def check_status(self):
        """Waits for a message and returns the task encoded in the message.
        """
        while True:
            await self.check_for_task() # checks if Event.task != None

    async def execute_task(self):


    async def read(self, msg:str) -> Awaitable:
        """Takes an incoming message and returns the encoded message.
        """


        # msg = socket.recv()

        try:
            assert msg[0] == HEADER
            assert msg[-1] == CR
            dispenser_id = msg[1:3]
            command = msg[3:5]
            amount = msg[5:-1]
        except:
            raise Exception('Invalid Command')
        match command:
            case 'DS':
                task = asyncio.create_task(self.dispense(dispenser_id, serving=amount))
            case 'CA':
                task = asyncio.create_task(self.calibrate(dispenser_id, test_mass=amount))
            case 'WE':
                task = asyncio.create_task(self.weigh(dispenser_id))
            case 'TR':
                task = asyncio.create_task(self.tare(dispenser_id))
            case 'CL':
                task = asyncio.create_task(self.clear(dispenser_id))
            case 'ST':
                task = asyncio.create_task(self.stop(dispenser_id))
            case None:
                task = None
        self.task = task
        return task
    
    async def dispense(self, dispenser_id, serving) -> str:
        """Dispenses a given amount from a given dispenser.
        """
        await self.dispensers[dispenser_id].dispense(serving=serving)
        return 'Success/status message'
            
    async def calibrate(self, dispenser_id, test_mass) -> str:
        """Calibrates a given dispenser with a given test mass.
        """
        await self.dispensers[dispenser_id].calibrate(test_mass=test_mass)
        return 'Success/status message'
    
    async def weigh(self, dispenser_id) -> str:
        """Measures the weight on a given dispenser.
        """
        await self.dispensers[dispenser_id].weigh()
        return 'Success/status message'
    
    async def tare(self, dispenser_id) -> str:
        """Tares a given dispenser.
        """
        await self.dispensers[dispenser_id].tare()
        return 'Success/status message'
    
    async def clear(self, dispenser_id) -> str:
        """Clears out the ingredient from a given dispenser.
        """
        await self.dispensers[dispenser_id].clear()
        return 'Success/status message'
    
    async def stop(self, dispenser_id) -> str:
        """Stops whatever task is being actively executed.
        """
        return