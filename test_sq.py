import math
import numpy as np
import time
import random

# Number of iterations
num_iterations = 100

# Initialize lists to store runtimes
runtimes_math = []
runtimes_numpy = []

# Perform the calculations using math.sqrt()
for _ in range(num_iterations):
    start_time = time.time()

    # Generate random values for x_dist, y_dist, and z
    x_dist = random.uniform(1.0, 10.0)
    y_dist = random.uniform(1.0, 10.0)
    z = random.uniform(1.0, 10.0)

    distance = math.sqrt(x_dist ** 2 + y_dist ** 2 + z ** 2)

    end_time = time.time()
    runtime = end_time - start_time
    runtimes_math.append(runtime)

# Perform the calculations using np.sqrt()
for _ in range(num_iterations):
    start_time = time.time()

    # Generate random values for x_dist, y_dist, and z as NumPy arrays
    x_dist = np.random.uniform(1.0, 10.0, size=(1,))
    y_dist = np.random.uniform(1.0, 10.0, size=(1,))
    z = np.random.uniform(1.0, 10.0, size=(1,))

    squared_distance = np.square(x_dist) + np.square(y_dist) + np.square(z)
    distance = np.sqrt(squared_distance)

    end_time = time.time()
    runtime = end_time - start_time
    runtimes_numpy.append(runtime)

# Calculate the mean runtimes
mean_runtime_math = sum(runtimes_math) / len(runtimes_math)
mean_runtime_numpy = sum(runtimes_numpy) / len(runtimes_numpy)

# Print the results
print(f"Mean runtime (math.sqrt()): {mean_runtime_math:.6f} seconds")
print(f"Mean runtime (np.sqrt()): {mean_runtime_numpy:.6f} seconds")
