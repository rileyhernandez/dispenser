from typing import Any, ClassVar, Dict, Mapping, Optional, Tuple, Sequence
from typing_extensions import Self
from tcp_client import tcp_write
import asyncio

HEADER = '\x00\x07'
CR = '\r'
DRIVE_TCP_PORT = 7776


class STF:
    def __init__(self, ip_address, steps, max_current):
        self.ip_address = ip_address
        self.steps = steps
        self.max_current = max_current

    async def drive_write(self, message: str):
        """ Reply format '\x00\x05XX=986\r"""
        message = HEADER + message + CR
        resp = await tcp_write(self.ip_address, DRIVE_TCP_PORT, message)
        print(resp)
        if resp[2] == '?':
            raise Exception('Invalid message sent to drive: ' + message + 'Resp: ' + resp)
        return resp[5:-1]
    
    async def set_power(self, power: float, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                        **kwargs):
        if power*10 >= 0.1:
            await self.drive_write(f'EG{self.steps}')
            await self.drive_write(f'ME')
            await self.drive_write(f'MC3')
            print(f"CC Command: CC{round(self.max_current*power)}")
            await self.drive_write(f'CC{round(self.max_current * power)}')
            await self.drive_write(f'CI{1 * power/2}')
        else:
            await self.drive_write(f'MD')
    
    async def go_for(self, rpm: float, revolutions: float, *, extra: Optional[Dict[str, Any]] = None,
                     timeout: Optional[float] = None, **kwargs):
        await self.drive_write(f'VE{round(rpm/60,2)}')
        await self.drive_write(f'DI{int(self.steps * revolutions)}')
        await self.drive_write(f'FL')
    
    async def change_speed(self, rpm: float):
        await self.drive_write(f'VE{round(rpm/60,2)}')
    
    async def stop(self):
        await self.drive_write(f'SK')