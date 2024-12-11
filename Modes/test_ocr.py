import pickle
import matplotlib.pyplot as plt

# Load the pickle files
with open("short.pkl", "rb") as short_file:
    short_times = pickle.load(short_file)

with open("long.pkl", "rb") as long_file:
    long_times = pickle.load(long_file)

# Create box plots for the two datasets
plt.figure(figsize=(8, 5))
plt.boxplot(
    [short_times, long_times],
    vert=True,
    patch_artist=True,
    labels=["100 words", "300 words"],
    boxprops=dict(facecolor='orange', color='black'),
    medianprops=dict(color='red', linewidth=2),
    whiskerprops=dict(color='black'),
    capprops=dict(color='black'),
    flierprops=dict(marker='o', color='red', alpha=0.5)
)

# Add labels and title
plt.ylabel("Time (seconds)")
plt.title("OCR processing times")

# Save the plot as a file
output_file = "comparison_box_plot.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Box plot saved as {output_file}")
