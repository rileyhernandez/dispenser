import time, asyncio
import numpy as np
import matplotlib.pyplot as plt
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

    async def weigh(self, samples=50):
        """ Calls the Scale.weigh() method.
        """
        weight = await self.scale.weigh(samples=samples)
        return weight

    async def calibrate(self, test_mass=393.8):
        """Runs the calibration process in Scale.py to recalculate the scale coefficients.
        """
        msg = await self.scale.calibrate()
        print(msg)

    
    async def get_average_readings(self):
        """DEFUNCT:
        Finds the average reading of each load cell and returns them in an array.
        """
        tasks = [asyncio.create_task(self.scale.get_cell_average[cell]()) for cell in range(len(self.scale.cells))]
        readings = await asyncio.gather(*tasks)
        return readings

    async def live_weigh(self):
        """Takes the instantaneous weight measurement."""
        weight = await self.scale.live_weigh()
        return weight

    async def dispense(self, serving, samples=200, sample_rate=50, rpm=500, offset=10, let_pass=3):
        """Dispenses the serving amount in grams running the conveyor motor at the desired rpm and step.
        The speed is proportionally controlled and dispenser stops once it dispenses the target weight 
        plus the offset amount
        """
        # Clear saved data
        self.reset_data()
        # Starts motor and runs in reverse; this allows scale priming to include noise from the motor
        await self.motor.enable()
        await self.motor.jog(-rpm)
        # Primes scale data to fill up sampling window
        window = []
        for _ in range(samples):
            reading = await self.live_weigh()
            window += [reading]
            await asyncio.sleep(1/sample_rate)
        # Sets initial median, weight, and time
        med = np.median(window)
        init_weight = med
        target = init_weight-serving
        passed = 0
        start_time = time.time()
        # Begins dispensing until end condition has been met let_passed times
        await self.motor.jog(rpm)
        while passed < let_pass:
            # Take new sample and move sampling window
            reading = await self.live_weigh()
            window = window[1:] + [reading]
            med = np.median(window)
            # Finds weight error and applies p-controller to conveyor speed
            err = (med-target)/serving
            new_rpm = min(max(err*rpm, 50), rpm)
            # await self.motor.jog(new_rpm)
            # Checks if end condition has been met
            if med <= target+offset:
                passed += 1
            # Logs time and weight data, sleeps until next sample
            curr_time = time.time() - start_time
            self.log_data(curr_time, med)
            await asyncio.sleep(1/sample_rate)

            print(f'Dispensed: {init_weight-med}')
        # Stops motor once target weight has been dispensed
        await self.motor.stop()
        await self.motor.disable()
        # Takes final weight measurement to display dispense amount and plots data
        end_weight = await self.weigh()
        print(f'Dispensed {init_weight-end_weight: .1f}')
        self.plot_data(file='dispense_data.png')

    async def dispense_old(self, serving, samples=50, sample_rate=2, outlier_ratio=0.5, rpm=500, offset=10, let_pass=3):
        """DEFUNCT:
        Dispenses the serving amount in grams running the conveyor motor at the desired rpm and step.
        The speed is proportionally controlled and dispenser stops once it dispenses the target weight 
        plus the offset amount
        """
        self.reset_data()
        await self.motor.enable()
        await self.motor.jog(-rpm)
        await asyncio.sleep(20)

        last_n = []
        for _ in range(samples):
            reading = await self.live_weigh()
            last_n += [reading]
            await asyncio.sleep(1/sample_rate)
        # weight = await self.weigh()
        # last_n = [weight for _ in range(samples)]
        
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

    async def tare(self, samples=100):
        """Tares the system by recalibrating the offset value.
        """
        offset = await self.weigh(samples=samples)
        self.scale.offset += offset

    def log_data(self, time, value, data='weight'):
        """Adds the inputted time and weight recordings to the dataset.
        """
        self.data['time'] += [time]
        self.data[data] += [value]
    
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
        plt.title(f'{data} {time.asctime(time.localtime())}')
        # plt.text(time.asctime(time.localtime()))
        plt.grid()
        plt.savefig(file)
        print("STD: ", np.std(weights))
        print('Range: +/-', max(abs(max(weights)-avg*(not normalize)), abs(min(weights)-avg*(not normalize))))

    def plot_spec(self, data='weight', file='magnitude_spectrum.png', Fs=True):
        weights = self.data[data]
        avg = sum(weights)/len(weights)
        weights_zeroed = [weight-avg for weight in weights]
        
        plt.close()
        if Fs:
            plt.magnitude_spectrum(weights_zeroed, 1/(self.data['time'][1]-self.data['time'][0]))
        else:
            plt.magnitude_spectrum(weights_zeroed)
        # plt.xlim(0.01, 1)
        # plt.ylim(0, Fs/2)
        plt.grid()
        plt.savefig(file)

    def reset_data(self, data='weight'):
        """Clears the dataset.
        """
        self.data['time'] = []
        self.data[data] = []

    async def test_avg(self, duration=10, filename='avg_data.png', sample_rate=25, samples=100, outlier_ratio=0.5):
        """Test function for collecting weight data with a moving average filter.
        """
        self.reset_data()

        last_n = []
        for _ in range(samples):
            weight = await self.live_weigh()
            last_n += [weight]
            time.sleep(1/sample_rate)
        
        start_time = time.time()
        curr_time = 0
        while curr_time < duration:
            weight = await self.live_weigh()
            last_n = last_n[1:] + [weight]
            avg = tools.prune(last_n, outlier_ratio)
            curr_time = time.time()-start_time
            self.data['time'] += [curr_time]
            self.data['weight'] += [avg]
            time.sleep(1/sample_rate)

        self.plot_data(file=filename)

    async def test_med(self, duration=10, filename='med_data.png', sample_rate=50, samples=200):
        """Test function for collecting weight data with a moving median filter.
        """
        self.reset_data()

        last_n = []
        for _ in range(samples):
            weight = await self.live_weigh()
            last_n += [weight]
            time.sleep(1/sample_rate)
        
        start_time = time.time()
        curr_time = 0
        while curr_time < duration:
            weight = await self.live_weigh()
            last_n = last_n[1:] + [weight]
            med = np.median(last_n)
            curr_time = time.time()-start_time
            self.data['time'] += [curr_time]
            self.data['weight'] += [med]
            time.sleep(1/sample_rate)

        self.plot_data(file=filename) 

    async def test_true(self, duration=10, filename='true_data.png', sample_rate=50):
        """Test function for collecting weight data without a filter.
        """
        self.reset_data()
        
        start_time = time.time()
        curr_time = 0
        while curr_time<duration:
            weight = await self.live_weigh()
            curr_time = time.time()-start_time
            self.data['time'] += [time.time()]
            self.data['weight'] += [weight]
            time.sleep(1/sample_rate)

        self.plot_data(file=filename) 

    async def test(self, duration=30, filename='test_data.png', sample_rate=50, samples=200, rpm=500):
        """...
        """
        self.reset_data()

        await self.motor.enable()
        await self.motor.jog(-rpm)
        last_n = []
        for _ in range(samples):
            weight = await self.live_weigh()
            last_n += [weight]
            time.sleep(1/sample_rate)
        
        start_time = time.time()
        curr_time = 0
        while curr_time < duration/2:
            weight = await self.live_weigh()
            last_n = last_n[1:] + [weight]
            med = np.median(last_n)
            curr_time = time.time()-start_time
            self.data['time'] += [curr_time]
            self.data['weight'] += [med]
            time.sleep(1/sample_rate)
        await self.motor.jog(rpm)
        while curr_time < duration:
            weight = await self.live_weigh()
            last_n = last_n[1:] + [weight]
            med = np.median(last_n)
            curr_time = time.time()-start_time
            self.data['time'] += [curr_time]
            self.data['weight'] += [med]
            time.sleep(1/sample_rate)

        await self.motor.stop()
        await self.motor.disable()
        self.plot_data(file=filename) 