from typing import Any, ClassVar, Dict, Mapping, Optional, Tuple, Sequence
from typing_extensions import Self
from tcp_client import tcp_write
import asyncio

HEADER = '\x02M0'
CR = '\x13'
DRIVE_TCP_PORT = 8888

class ClearCore:
    def __init__(self, ip_address, steps):
        self.ip_address = ip_address
        self.steps = steps
        self.last_pos = 0.0
        asyncio.run(self.enable())

    async def drive_write(self, cmd, amt:str='') -> str:
        """ Takes commands and sends them as messages to the motor.
        """
        message = HEADER + cmd + str(amt) + CR
        resp = await tcp_write(self.ip_address, DRIVE_TCP_PORT, message)
        # print(resp)
        if resp == HEADER+'63':
            raise Exception(f'Invalid message sent to drive: {message} Resp: {resp}')
        return resp
    
    async def enable(self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                        **kwargs):
        resp = await self.drive_write('EN')
        return resp
    
    async def disable(self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None,
                        **kwargs):
        resp = await self.drive_write('DE')
        return resp

    async def info(self):
        resp = await self.drive_write('GS')
        return resp
    
    async def go_for(self, rpm: float, revolutions: float, *, extra: Optional[Dict[str, Any]] = None,
                     timeout: Optional[float] = None, **kwargs):
        await self.change_speed(rpm)
        resp = await self.drive_write('RM', revolutions)
        return resp
    
    async def go_to(self, rpm: float, position_revolutions: float, *, extra: Optional[Dict[str, Any]] = None,
                    timeout: Optional[float] = None, **kwargs):
        await self.change_speed(rpm)
        resp = await self.drive_write('AM', position_revolutions)
        return resp
    
    async def jog(self, rpm: float):
        rpm = await self.check_speed(rpm)
        resp = await self.drive_write('JG', rpm)
        return resp
    
    async def stop(self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs):
        resp = await self.drive_write('AS')
        return resp
    
    async def change_speed(self, rpm: float, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs):
        rpm = await self.check_speed(rpm)
        resp = await self.drive_write('SV', rpm)
        return resp
    
    async def check_speed(self, rpm):
        if rpm > 2000:
            raise Exception('WARNING! Speed is too high: {rpm}')
        return int(rpm)