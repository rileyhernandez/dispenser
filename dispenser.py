import time, serial, asyncio
import numpy as np
import matplotlib.pyplot as plt
from STF06_IP import STF
from load_cell import LoadCell


class Dispenser:
    def __init__(self, conveyor_motor, load_cells):
        self.conveyor_motor = conveyor_motor
        self.load_cells = load_cells
        self.offset = 0
        self.data = {}
        self.data['time'] = []
        self.data['weight'] = []

        self.coefficients = np.array([[ 1.05367982e+07],
        [ 5.58626571e+06],
        [ 1.22174287e+07],
        [ 1.08556060e+07],
        [-2.24938354e+03]])

    async def weigh(self):
        """Takes dot product of the array of each load cell's average readings and the systems coefficients.
        The result minus the system's offset weight is returned.
        """
        readings = await self.get_average_readings()
        weights = [readings[i]*self.coefficients[i] for i in range(len(readings))]
        return float(sum(weights) - self.offset)

    async def calibrate(self, test_mass=393.8):
        """Calibrates the load cell system to determine what its coefficients are in order to account for 
        load cell variation and assembly tolerance.
        Then the system is tared.
        """
        A, b = [], []
        for trial in range(len(self.load_cells)):
            try:
                input('Place/move test mass and press Enter')
            except(Exception, KeyboardInterrupt):
                pass
            trial_readings = await self.get_average_readings()
            trial_readings += [1] 
            A += [trial_readings]
            b += [[test_mass]]
       
        try:
            input('Remove test mass and press Enter')
        except(Exception, KeyboardInterrupt):
            pass
        trial_readings = await self.get_average_readings()
        trial_readings += [1]
        A += [trial_readings]
        b += [[0]]

        A, b = np.array(A), np.array(b)
        x = np.linalg.solve(A, b)
        self.coefficients = x
        await self.tare()
    
    async def get_average_readings(self):
        """Finds the average reading of each load cell and returns them in an array.
        Optional arguments: samples, sample_freq
        """
        tasks = [asyncio.create_task(self.load_cells[cell].average_reading()) for cell in range(len(self.load_cells))]
        readings = await asyncio.gather(*tasks)
        return readings

    async def live_weigh(self):
        """Finds the live reading of each load cell and dot products its array with the systems coefficients.
        The result the system's offset weight is returned.
        """
        tasks = [asyncio.create_task(self.load_cells[cell].read()) for cell in range(len(self.load_cells))]
        readings = await asyncio.gather(*tasks)
        weights = [readings[i]*self.coefficients[i] for i in range(len(readings))]
        return float(sum(weights)-self.offset)

    async def set_motor(self, ip='192.168.1.10', steps=200, max_current=2, power=1):
        self.motor = STF(ip, steps, max_current)

    async def dispense(self, serving, rpm=100, step=1000, offset=5, n=10, inc_step=0.25):
        """Dispenses the serving amount in grams running the conveyor motor at the desired rpm and step.
        The speed is proportionally controlled and dispenser stops once it dispenses the target weight 
        plus the offset amount
        """
        self.reset_data()
        def prune(weights, n):
            outliers = []
            for i in range(n):
                outliers += [max(weights), min(weights)]
            return (sum(weights)-sum(outliers))/(len(weights)-len(outliers))
        last_n = []
        for i in range(n):
            now = await self.live_weigh()
            last_n += [now]
            time.sleep(0.1)
        starting_mass = sum(last_n)/len(last_n)
        target_mass = starting_mass - serving
        await self.conveyor_motor.go_for(rpm, step)
        avg = sum(last_n)/len(last_n)
        while avg > target_mass+offset:
            curr_weight = await self.live_weigh()
            last_n = last_n[1:] + [curr_weight]
            avg = prune(last_n, 5)
            self.log_data(time.time(), curr_weight)
            self.conveyor_motor.change_speed(((avg-target_mass)/serving)*rpm)
            time.sleep(0.05)
        await self.conveyor_motor.stop()
        weight = await self.weigh()
        while weight > target_mass+3:
            await self.conveyor_motor.go_for(25, inc_step)
            weight = await self.weigh()
        print('Dispensed ' + str(starting_mass-weight) + 'g')
    
    async def tare(self):
        """Tares the system by recalibrating the offset value
        """
        self.offset = await self.weigh()

    def log_data(self, time, weight):
        """Adds the inputted time and weight recordings to the dataset
        """
        self.data['time'] += [time]
        self.data['weight'] += [weight]
    
    def plot_data(self, normalize=True):
        """Plots the time and weight data in the dataset
        """
        times = [t-self.data['time'][0] for t in self.data['time']]
        if normalize:
            avg = sum(self.data['weight'])/len(self.data['weight'])
            weights = [self.data['weight'][weight]-avg for weight in range(len(self.data['weight']))]
        else:
            weights = self.data['weight']
        plt.close()
        plt.plot(times, weights)
        plt.xlabel('Time')
        plt.ylabel('Average Weight')
        plt.title('Average Weight vs Time')
        plt.grid()
        plt.savefig('data.png')
        print("STD: ", np.std(self.data['weight']))
        print('Range: +/-', (max(self.data['weight'])-min(self.data['weight']))/2)

    def reset_data(self):
        """Clears the dataset
        """
        self.data['time'] = []
        self.data['weight'] = []
        
    async def test(self, timestep=0.1, samples=100):
        """Collects data over an inputted amount of samples
        """
        self.reset_data()
        for i in range(samples):
            self.data['time'] += [time.time()]
            weight = await self.live_weigh()
            self.data['weight'] += [weight]
            time.sleep(timestep)
    
    async def test_avg(self, t=10, sample_rate=25, samples=100, outlier_ratio=0.50):
        """Collects data over an inputted amount of samples recording each data point
        as the average of the last 10 weights and removing outliers"""
        
        def prune(data_set, ratio=outlier_ratio):
            """Function that takes in a data set and returns the average, excluding the amount
            of outliers specified.
            """
            outliers = []
            for _ in range(int(ratio*len(data_set)/2)):
                outliers += [max(data_set), min(data_set)]
            weight = (sum(data_set)-sum(outliers))/(len(data_set)-len(outliers))
            return weight
        self.reset_data()
        last_n = []
        for _ in range(samples):
            now = await self.live_weigh()
            last_n += [now]
            time.sleep(1/sample_rate)
        for _ in range(t*sample_rate):
            curr_weight = await self.live_weigh()
            last_n = last_n[1:] + [curr_weight]
            try:
                avg = prune(last_n)
            except:
                print("DEBUG 1: ", last_n)
                return
            self.log_data(time.time(), avg)
            time.sleep(1/sample_rate)
