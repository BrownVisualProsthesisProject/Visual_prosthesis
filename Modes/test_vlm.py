import time
import pickle
import ollama

# Define the model and image path
model = "llava:13b"  # Replace with your actual model name
image_path = "park.jpg"

# Collect processing times
times = []
for i in range(30):
    start_time = time.time()
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "user", "content": "Describe this image in a sentence", "images": [image_path]}
        ],
        stream=False
    )
    print(response)

    end_time = time.time()
    times.append(end_time - start_time)

# Save the times list to a pickle file
pickle_file = "ollama_processing_times.pkl"
with open(pickle_file, "wb") as file:
    pickle.dump(times, file)

print(f"Processing times saved to {pickle_file}")
