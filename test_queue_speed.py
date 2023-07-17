import time
import collections
import torch
import random

def append_with_deque():
    audio_deque = collections.deque()
    start_time = time.time()

    for _ in range(1000):
        new_element = torch.randn(1024)
        audio_deque.append(new_element)

    concatenated_tensor = torch.cat(tuple(audio_deque), dim=0)

    end_time = time.time()
    elapsed_time = end_time - start_time
    return elapsed_time

def append_with_torch():
    x = torch.tensor([])
    start_time = time.time()

    for _ in range(1000):
        new_element = torch.randn(1024)
        x = torch.cat((x, new_element.unsqueeze(0)), dim=0)

    end_time = time.time()
    elapsed_time = end_time - start_time
    return elapsed_time

# Measure time taken with deque
deque_time = append_with_deque()

# Measure time taken with torch.cat()
torch_time = append_with_torch()

print("Time taken with deque: ", deque_time)
print("Time taken with torch.cat(): ", torch_time)
