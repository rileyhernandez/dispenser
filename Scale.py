from Phidget22.Phidget import *
from Phidget22.Devices.VoltageRatioInput import *
from tools import prune, dot_product
import numpy as np
import matplotlib.pyplot as plt
import asyncio

class Scale:
    def __init__(self, SIN):
        self.cells = [VoltageRatioInput() for _ in range(4)]
        for cell in range(len(self.cells)):
            self.cells[cell].setDeviceSerialNumber(SIN)
            self.cells[cell].setChannel(cell)
            self.cells[cell].openWaitForAttachment(1000)
            self.cells[cell].setDataInterval(self.cells[cell].getMinDataInterval())
        self.offset = 2920
        self.coefficients = [1.10669791e+07, 2.53250106e+06, 1.21621447e+07, 9.56128040e+06, -3.42132575e+03]
        self.data = {'c0':[], 'c1':[], 'c2':[], 'c3':[], 'weights':[]}

    async def get_readings(self):
        coros = [self.get_cell_reading(cell) for cell in range(len(self.cells))]
        readings = await asyncio.gather(*coros)
        return readings
    
    async def get_cell_reading(self, cell):
        reading = self.cells[cell].getVoltageRatio()
        self.data[f'c{cell}'] += [reading*self.coefficients[cell]]
        return reading
    
    async def get_cell_average(self, cell, samples=100, sample_rate=25, outliers_ratio=0.5):
        readings = []
        for _ in range(samples):
            reading = await self.get_cell_reading(cell)
            readings += [reading]
            await asyncio.sleep(1/sample_rate)
        avg = prune(readings, outliers_ratio)
        return avg

    async def live_weigh(self):
        """Measures instantaneous weight
        """
        # Collects instantaneous cell readings
        readings = await self.get_readings()
        # Takes dot product of readings and coefficients to calculate 
        weight = sum([readings[reading]*self.coefficients[reading] for reading in range(len(readings))])
        # Returns weight minus offset (from tare)
        return weight-self.offset

    async def weigh(self, samples=100, sample_rate=25, outliers_ratio=0.50):
        """Takes the average weight over a given time period for a given number of samples
        at a given sample rate while removing outliers
        """
        coros = [self.get_cell_average(cell,samples,sample_rate,outliers_ratio) for cell in range(len(self.cells))]
        average_readings = await asyncio.gather(*coros)
        weight = dot_product(average_readings, self.coefficients)
        return weight-self.offset
    
    async def calibrate(self, test_mass=393.8):
        """Calibrates the load cell system to determine what its coefficients are in order to account for 
        load cell variation and assembly tolerance.
        Then the system is tared.
        """
        # Conducts weight trials and collects data
        A, b = [], []
        for trial in range(len(self.cells)):
            try:
                input('Place/move test mass and press Enter')
            except(Exception, KeyboardInterrupt):
                pass
            coros = [self.get_cell_average(cell) for cell in range(len(self.cells))]
            trial_readings = await asyncio.gather(*coros)
            trial_readings += [1]
            A += [trial_readings]
            b += [[test_mass]]
        try:
            input('Remove test mass and press Enter')
        except(Exception, KeyboardInterrupt):
            pass
        # Conducts final trial (no weight)
        coros = [self.get_cell_average(cell) for cell in range(len(self.cells))]
        trial_readings = await asyncio.gather(*coros)
        trial_readings += [1]
        A += [trial_readings]
        b += [[0]]

        # Inputs trial data into matrices and solves 'Ax = b'
        A, b = np.array(A), np.array(b)
        x = np.linalg.solve(A, b)
        # Converts x into a list and saves it as an attribute
        x.reshape(1, -1).tolist()[0]
        self.coefficients = [list(i)[0] for i in x]

        # Tares scale and ends method
        # await self.tare()
        self.offset = await self.weigh()
        return 'Calibration Successful'
    
    async def tare(self):
        self.offset += self.weigh()

    # async def weigh(self, samples=100, sample_rate=25, outliers_ratio=0.50):
    #     """Takes the average weight over a given time period for a given number of samples
    #     at a given sample rate while removing outliers
    #     """
    #     weights = []
    #     for _ in range(samples):
    #         reading = await self.live_weigh()
    #         weights += [reading]
    #         await asyncio.sleep(1/sample_rate)
    #     avg = prune(weights, outliers_ratio)
    #     return avg


    
    # def set_cell(self):
    #     self.input.setChannel(self.channel)
    #     self.input.openWaitForAttachment(1000)
    #     self.input.setDataInterval(self.input.getMinDataInterval())
    
    # async def read(self):
    #     reading = self.input.getVoltageRatio()
    #     return reading
    
    # async def average_reading(self, samples=64, sample_freq=0.008):
    #     average = 0
    #     for i in range(samples):
    #         reading = await self.read()
    #         # reading = self.input.getVoltageRatio()
    #         average += reading
    #         time.sleep(sample_freq)
    #     average = average/samples
    #     return average