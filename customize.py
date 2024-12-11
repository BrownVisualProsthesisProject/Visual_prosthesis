import matplotlib.pyplot as plt

# Path to your .dat file
dat_file = "mprofile.dat"

# Initialize lists for storing data
timestamps = []
memory_usage = []

# Read the .dat file
with open(dat_file, "r") as file:
    for line in file:
        if line.startswith("MEM"):  # Only process lines starting with "MEM"
            try:
                _, memory, timestamp = line.split()  # Split the line into components
                memory_usage.append(float(memory))
                timestamps.append(float(timestamp))
            except ValueError:
                # Skip lines that don't have the expected format
                continue

# Normalize time so it starts at 0
if timestamps:
    start_time = timestamps[0]
    timestamps = [t - start_time for t in timestamps]

# Plot the normalized data
plt.figure(figsize=(10, 6))
plt.plot(timestamps, memory_usage, label="Memory Usage", color="orange", linewidth=2)

# Adding customizations
plt.title("Memory Usage Over Time", fontsize=16)
plt.xlabel("Time (seconds)", fontsize=14)
plt.ylabel("Memory Usage (MiB)", fontsize=14)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(fontsize=12)

# Save the plot as an image file
output_file = "normalized_memory_usage_plot.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Customized normalized plot saved as {output_file}")

# Optionally display the plot
# plt.show()
