import time, asyncio
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter, freqz
import tools as tools
from ClearCore import ClearCore
from Scale import Scale


class Dispenser:
    def __init__(self, motor: ClearCore, scale: Scale):
        self.motor = motor
        self.scale = scale
        self.offset = 0
        self.data = {}
        self.data['time'] = []
        self.data['weight'] = []

    async def weigh(self):
        weight = await self.scale.weigh()
        return weight

    async def calibrate(self, test_mass=393.8):
        msg = await self.scale.calibrate()
        print(msg)

    
    async def get_average_readings(self):
        """Finds the average reading of each load cell and returns them in an array.
        Optional arguments: samples, sample_freq
        """
        tasks = [asyncio.create_task(self.scale.get_cell_average[cell]()) for cell in range(len(self.scale.cells))]
        readings = await asyncio.gather(*tasks)
        return readings

    async def live_weigh(self):
        weight = await self.scale.live_weigh()
        return weight

    async def dispense(self, serving, samples=50, sample_rate=2, outlier_ratio=0.5, rpm=500, offset=10, let_pass=3):
        """Dispenses the serving amount in grams running the conveyor motor at the desired rpm and step.
        The speed is proportionally controlled and dispenser stops once it dispenses the target weight 
        plus the offset amount
        """
        self.reset_data()
        await self.motor.enable()
        await asyncio.sleep(2)

        # last_n = []
        # for _ in range(samples):
        #     reading = await self.live_weigh()
        #     last_n += [reading]
        #     await asyncio.sleep(1/sample_rate)
        await self.motor.jog(-500)
        weight = await self.weigh()
        last_n = [weight for _ in range(samples)]
        
        avg = tools.prune(last_n)
        init_weight = avg
        target = init_weight-serving

        passed = 0
        start_time = time.time()
        await self.motor.jog(rpm)
        while passed < let_pass:
            reading = await self.live_weigh()
            # print('DEBUG: ', last_n)
            last_n = last_n[1:] + [reading]
            # print('DEBUG: ', last_n)
            avg = tools.prune(last_n, outlier_ratio)

            err = (avg-target)/serving
            new_rpm = min(max(err*rpm, 50), rpm)
            print(f'DEBUG: {err} {new_rpm}')
            await self.motor.jog(new_rpm)
            await asyncio.sleep(1/sample_rate)
            
            if avg <= target+offset:
                passed += 1

            curr_time = time.time() - start_time
            self.log_data(curr_time, avg)
        await self.motor.stop()
        await self.motor.disable()
        end_weight = await self.weigh()
        print(f'Dispensed {init_weight-end_weight: .1f}')
        self.plot_data(file='dispense_data.png')

    async def calibrate(self):
        await self.scale.calibrate()

    async def tare(self):
        """Tares the system by recalibrating the offset value
        """
        self.scale.offset = await self.weigh()

    def log_data(self, time, weight):
        """Adds the inputted time and weight recordings to the dataset
        """
        self.data['time'] += [time]
        self.data['weight'] += [weight]
    
    def plot_data(self, data='weight', file='data.png', normalize=True):
        """Plots the time and weight data in the dataset
        """
        times = [t-self.data['time'][0] for t in self.data['time']]
        avg = sum(self.data[data])/len(self.data[data])
        if normalize:
            weights = [self.data[data][weight]-avg for weight in range(len(self.data[data]))]
        else:
            weights = self.data[data]
        plt.close()
        plt.plot(times, weights)
        plt.xlabel('Time [s]')
        plt.ylabel('Weight [g]')
        plt.title(data)
        plt.text(time.asctime(time.localtime()))
        plt.grid()
        plt.savefig(file)
        print("STD: ", np.std(weights))
        print('Range: +/-', max(abs(max(weights)-avg*(not normalize)), abs(min(weights)-avg*(not normalize))))

    def reset_data(self):
        """Clears the dataset
        """
        self.data['time'] = []
        self.data['weight'] = []

    async def test(self, filename='data.png', sample_rate=25, samples=100):
        """Collects data over an inputted amount of samples
        """
        self.reset_data()

        last_n = []
        for _ in range(30):
            weight = await self.live_weigh()
            last_n += [weight]
            time.sleep(1/sample_rate)
        
        for _ in range(samples):
            weight = await self.live_weigh()
            last_n = last_n[1:] + [weight]
            avg = tools.prune(last_n)
            self.data['time'] += [time.time()]
            self.data['weight'] += [avg]
            time.sleep(1/sample_rate)

        fs = sample_rate
        cutoff = 5
        
        self.data['filtered'] = self.butter_lowpass_filter(self.data['weight'], cutoff, fs)

        self.data['time'] = self.data['time'][15:]
        self.data['filtered'] = self.data['filtered'][15:]

        self.plot_data(data='filtered', file=filename)
    
    #####################################################################################################

    def butter_lowpass(self, cutoff, fs, order=5):
        nyquist = 0.5*fs
        normal_cutoff = cutoff/nyquist
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return b, a

    def butter_lowpass_filter(self, data, cutoff, fs, order=5):
        b, a = self.butter_lowpass(cutoff, fs, order=order)
        y = lfilter(b,a, data)
        return y
    
    ####################################################################################################
    async def test_avg(self, filename='data.png', sample_rate=25, samples=100):
        """Collects data over an inputted amount of samples
        """
        self.reset_data()

        last_n = []
        for _ in range(30):
            weight = await self.live_weigh()
            last_n += [weight]
            time.sleep(1/sample_rate)
        
        for _ in range(samples):
            weight = await self.live_weigh()
            last_n = last_n[1:] + [weight]
            avg = tools.prune(last_n)
            self.data['time'] += [time.time()]
            self.data['weight'] += [avg]
            time.sleep(1/sample_rate)

        self.plot_data(filename)
    
    async def test_avg(self, t=10, sample_rate=25, samples=100, outlier_ratio=0.50):
        """Collects data over an inputted amount of samples recording each data point
        as the average of the last 10 weights and removing outliers"""
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
                avg = tools.prune(last_n)
            except:
                print("DEBUG 1: ", last_n)
                return
            self.log_data(time.time(), avg)
            time.sleep(1/sample_rate)
