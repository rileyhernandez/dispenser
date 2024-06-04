from Phidget22.Phidget import *
from Phidget22.Devices.VoltageRatioInput import *
from tools import dot_product
import numpy as np
import asyncio
import csv

class Scale:
    def __init__(self, SIN):
        self.cells = [VoltageRatioInput() for _ in range(4)]
        for cell in range(len(self.cells)):
            self.cells[cell].setDeviceSerialNumber(SIN)
            self.cells[cell].setChannel(cell)
            self.cells[cell].openWaitForAttachment(2000)
            self.cells[cell].setDataInterval(self.cells[cell].getMinDataInterval())
        self.offset = 4122.65
        self.data = {'c0':[], 'c1':[], 'c2':[], 'c3':[], 'weight':[]}
        self.import_coefficients()

    def import_coefficients(self):
        """Imports saved scale coefficients from csv.
        """
        with open('data/scale_coefficients.csv', newline='') as f:
            reader = csv.reader(f)
            data = list(reader)[0]
        coefficients = [float(i) for i in data]
        self.coefficients = coefficients
    
    def write_coefficients(self):
        """Writes newly calculated scale coefficients to csv
        """
        new_coefficients = [self.coefficients]
        with open('data/scale_coefficients.csv', 'wt') as fp:
            writer = csv.writer(fp, delimiter=',')
            writer.writerows(new_coefficients)

    async def get_readings(self):
        """Gets all cell readings from Phidget.
        """
        coros = [self.get_cell_reading(cell) for cell in range(len(self.cells))]
        readings = await asyncio.gather(*coros)
        return readings
    
    async def get_cell_reading(self, cell):
        """Gets reading of a particular cell from Phidget.
        """
        reading = self.cells[cell].getVoltageRatio()
        self.data[f'c{cell}'] += [reading*self.coefficients[cell]]
        return reading
    
    async def get_cell_median(self, cell, samples=1000, sample_rate=50):
        """Finds the median of a given number of weight samples at a given rate.
        Default is 1000 samples over 20 seconds.
        """
        readings = []
        for _ in range(samples):
            reading = await self.get_cell_reading(cell)
            readings += [reading]
            await asyncio.sleep(1/sample_rate)
        med = np.median(readings)
        return med

    async def live_weigh(self):
        """Measures instantaneous weight.
        """
        # Collects instantaneous cell readings
        readings = await self.get_readings()
        # Takes dot product of readings and coefficients to calculate 
        weight = sum([readings[reading]*self.coefficients[reading] for reading in range(len(readings))])
        # Returns weight minus offset (from tare)
        return weight-self.offset

    async def weigh(self, samples=100, sample_rate=50):
        """Takes the median weight over a given time period for a given number of samples
        at a given sample rate while removing outliers.
        """
        self.clear_data()
        coros = [self.get_cell_median(cell,samples,sample_rate) for cell in range(len(self.cells))]
        median_readings = await asyncio.gather(*coros)
        weight = dot_product(median_readings, self.coefficients)
        return weight-self.offset
    
    async def calibrate(self, test_mass=393.8):
        """Calibrates the load cell system to determine what its coefficients are in order to account for 
        load cell variation and assembly tolerance.
        Then the system is tared.
        """
        self.clear_data()
        # Conducts weight trials and collects data
        A, b = [], []
        for _ in range(len(self.cells)):
            try:
                input('Place/move test mass and press Enter')
            except(Exception, KeyboardInterrupt):
                pass
            coros = [self.get_cell_median(cell) for cell in range(len(self.cells))]
            trial_readings = await asyncio.gather(*coros)
            trial_readings += [1]
            A += [trial_readings]
            b += [[test_mass]]
        try:
            input('Remove test mass and press Enter')
        except(Exception, KeyboardInterrupt):
            pass
        # Conducts final trial (no weight)
        coros = [self.get_cell_median(cell) for cell in range(len(self.cells))]
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
        self.write_coefficients()

        # Tares scale and ends method
        # await self.tare()
        # self.offset = await self.weigh()
        return 'Calibration Successful'
    
    async def tare(self):
        self.offset += self.weigh()
        self.clear_data()

    def clear_data(self):
        self.data = {'c0':[], 'c1':[], 'c2':[], 'c3':[], 'weight':[]}