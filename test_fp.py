import torch
import time
import torchvision.transforms as T
from torchvision.models import detection

# Load the YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

# Set device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

# Generate a random RGB image of size 1200x700 and apply transformations
image = torch.randn(1,3,736,1280)

# Half precision inference
model.half()
half_precision_times = []
for _ in range(100):
    start_time = time.time()
    with torch.no_grad():
        _ = model(image)
    end_time = time.time()
    elapsed_time = end_time - start_time
    half_precision_times.append(elapsed_time)

# Full precision inference
model.float()
full_precision_times = []
for _ in range(100):
    start_time = time.time()
    with torch.no_grad():
        _ = model(image)
    end_time = time.time()
    elapsed_time = end_time - start_time
    full_precision_times.append(elapsed_time)

# Calculate the average time for half and full precision
half_precision_avg_time = sum(half_precision_times) / len(half_precision_times)
full_precision_avg_time = sum(full_precision_times) / len(full_precision_times)

# Print the results
print(f"Average time for half precision: {half_precision_avg_time} seconds")
print(f"Average time for full precision: {full_precision_avg_time} seconds")