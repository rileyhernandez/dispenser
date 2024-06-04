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

    async def weigh(self, samples=50, sample_rate=100):
        """ Calls the Scale.weigh() method. 
        Default takes the median of 50 samples over 0.5 seconds.
        """
        weight = await self.scale.weigh(samples=samples, sample_rate=sample_rate)
        return weight

    async def calibrate(self, test_mass=393.8):
        """Runs the calibration process in Scale.py to recalculate the scale coefficients.
        Default uses the tape measure as the test mass.
        """
        msg = await self.scale.calibrate(test_mass=test_mass)
        print(msg)
        await self.tare()

    async def live_weigh(self):
        """Takes the instantaneous weight measurement.
        """
        weight = await self.scale.live_weigh()
        return weight

    async def dispense(self, serving, sample_rate=50, cutoff=0.5, rpm=500, offset=10, let_pass=3):
        """Dispenses the serving amount in grams running the conveyor motor at the desired rpm and step.
        The speed is proportionally controlled and dispenser stops once it dispenses the target weight 
        plus the offset amount.
        """
        # Set LPF values
        T = 1/sample_rate
        RC = 1/(cutoff*2*np.pi)
        a = T/(T+RC)
        b = RC/(T+RC)
        # Clear saved data
        self.reset_data()
        # Starts motor and runs in reverse; this allows scale priming to include noise from the motor
        await self.motor.enable()
        await asyncio.sleep(0.25)
        await self.motor.jog(-2000)
        await asyncio.sleep(3)
        # Initialize variables for dispensing loop
        passed = 0
        init_weight = await self.weigh(samples=200, sample_rate=100)
        target = init_weight-serving
        start_time = time.time()
        last_sent = 0
        self.log_data(time=0, value=init_weight)
        # Begins dispensing until end condition has been met let_passed times
        await self.motor.jog(rpm)
        while passed < let_pass:
            # Take new sample and apply LPF
            reading = await self.live_weigh()
            weight = a*reading + b*self.data['weight'][-1]
            curr_time = time.time() - start_time
            # Logs time and weight data
            self.log_data(curr_time, weight)
            # Finds weight error to calculate new conveyor speed for p-control
            err = (weight-target)/serving
            new_rpm = min(max(err*rpm, 50), rpm)
            # Applies new RPM but limits motor changes to once every 0.25 seconds
            if curr_time-last_sent > 0.25:
                last_sent = curr_time
                await self.motor.jog(new_rpm)
            # Checks if end condition has been met
            if weight <= target+offset:
                passed += 1
            # Sleeps until time for next sample
            await asyncio.sleep(1/sample_rate)
        # Stops motor once target weight has been dispensed
        await self.motor.stop()
        # Takes final weight measurement to display dispense amount and plots data
        end_weight = await self.weigh()
        print(f'Dispensed {init_weight-end_weight: .1f}')
        self.plot_data(file='dispense_data.png', normalize=False)
        # Disables motor
        await self.motor.disable()

    async def tare(self, samples=100, sample_rate=100):
        """Tares the system by recalibrating the offset value.
        Default uses 100 samples over 1 second
        """
        offset = await self.weigh(samples=samples, sample_rate=sample_rate)
        self.scale.offset += offset

    async def clear(self, rpm=2000, duration=30):
        await self.motor.enable()
        await asyncio.sleep(0.25)
        await self.motor.jog(2000)
        await asyncio.sleep(duration)
        await self.motor.stop()
        await asyncio.sleep(0.25)
        await self.motor.disable()

    def log_data(self, time, value, data='weight'):
        """Adds the inputted time and weight recordings to the dataset.
        """
        self.data['time'] += [time]
        self.data[data] += [value]
    
    def plot_data(self, data='weight', file='data.png', normalize=True):
        """Plots the time and weight data in the dataset
        """
        times = [t-self.data['time'][0] for t in self.data['time']]
        if normalize:
            avg = sum(self.data[data])/len(self.data[data])
            weights = [self.data[data][weight]-avg for weight in range(len(self.data[data]))]
        else:
            weights = self.data[data]
        plt.close()
        plt.plot(times, weights)
        plt.xlabel('Time [s]')
        plt.ylabel('Weight [g]')
        plt.title(f'{data} {time.asctime(time.localtime())}')
        plt.grid()
        plt.savefig(f'data/{file}')
        print("STD: ", np.std(weights))
        print('Range: +/-', max(abs(max(weights)-avg*(not normalize)), abs(min(weights)-avg*(not normalize))))

    def plot_spec(self, data='weight', file='magnitude_spectrum.png', Fs=True):
        """Plots frequency spectrum of measured weight data.
        """
        weights = self.data[data]
        avg = sum(weights)/len(weights)
        weights_zeroed = [weight-avg for weight in weights]
        
        plt.close()
        if Fs:
            plt.magnitude_spectrum(weights_zeroed, 1/(self.data['time'][1]-self.data['time'][0]))
        else:
            plt.magnitude_spectrum(weights_zeroed)
        plt.grid()
        plt.savefig(f'data/{file}')

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

    async def test_filter(self, duration=10, filename='filter_data.png', sample_rate=100, cutoff=0.5):
        """Test function for collecting weight data without a filter.
        """
        self.reset_data()

        T = 1/sample_rate
        RC = 1/(cutoff*2*np.pi)
        a = T/(T+RC)
        b = RC/(T+RC)
        
        start_time = time.time()
        curr_time = 0
        while curr_time<duration:
            weight = await self.live_weigh()
            if self.data['weight'] == []:
                filtered_weight = weight
            else:
                filtered_weight = a*weight + b*self.data['weight'][-1]
            curr_time = time.time()-start_time
            self.log_data(curr_time, filtered_weight)
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