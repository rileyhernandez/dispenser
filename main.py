import asyncio, time
import numpy as np
import matplotlib.pyplot as plt
from load_cell import LoadCell

scale = LoadCell()

start_time = time.time()
print(f'Weight: {asyncio.run(scale.weigh()):.1f}g')
end_time = time.time()
print(f'Time elapsed: {end_time-start_time:.1f} s')

scale.plot()

def plot(data):
    plt.close()
    plt.plot(data)
    plt.grid()
    plt.savefig('data.png')

# weights = []
# for _ in range(10):
#     weight = asyncio.run(scale.weigh())
#     weights += [weight]