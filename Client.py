from typing import Dict
from Dispenser import Dispenser
import asyncio

from typing import Awaitable

HEADER = '\x02'
CR = '\x13'

class Client:
    def __init__(self, dispensers:Dict[str, Dispenser]):
        self.dispensers = dispensers # dictionary of dispensers with key='D0'
        self.task: None | Awaitable = None

    async def run(self):
        """Waits for a message; once one is received it coruns receive() and read().
        If another message is received, it is placed in the queue by its priority.
        """
        if self.task:
            asyncio.gather(self.receive(), self.task())
        else:
            self.task = await self.receive()

    async def receive(self):
        """Waits for a message and returns the task encoded in the message.
        """
        msg = await something()
        task = await self.read(msg)
        return task

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