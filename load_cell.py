from Phidget22.Phidget import *
from Phidget22.Devices.VoltageRatioInput import *
import time

class LoadCell:
    def __init__(self, channel):
        self.channel = channel
        self.input = VoltageRatioInput()
        
        self.set_cell()
    
    def set_cell(self):
        self.input.setChannel(self.channel)
        self.input.openWaitForAttachment(1000)
        self.input.setDataInterval(self.input.getMinDataInterval())
    
    async def read(self):
        reading = self.input.getVoltageRatio()
        return reading
    
    async def average_reading(self, samples=64, sample_freq=0.008):
        average = 0
        for i in range(samples):
            reading = await self.read()
            # reading = self.input.getVoltageRatio()
            average += reading
            time.sleep(sample_freq)
        average = average/samples
        return average