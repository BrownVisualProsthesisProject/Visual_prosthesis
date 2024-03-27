import pandas as pd
import random

# Read the original CSV file
df = pd.read_csv('labels_objects.csv')

# Extract the labels and objects columns
labels = df['labels'].tolist()
objects = df['object_name'].tolist()

# Create lists for target and distractor positions
positions = list(range(1, 8))

print(positions)
# Shuffle the objects to ensure randomness
random.shuffle(objects)

# Create a DataFrame for the new CSV
new_data = []

# Fill the first 7 rows with target and distractor positions
for i in range(7):
    target_position = i+1
    target_object = random.choice(objects)
    objects.remove(target_object)
    
    distractor_objects = random.sample(objects, 2)
    distractor_positions = random.sample(positions[:i] + positions[i+1:], 2)
    
    row = {
        'target position': target_position,
        'target object': target_object,
        'distractor object position 1': distractor_positions[0],
        'distractor object 1': distractor_objects[0],
        'distractor object position 2': distractor_positions[1],
        'distractor object 2': distractor_objects[1],
    }
    new_data.append(row)

# Fill the last 3 rows with random target positions and other columns filled similarly
for _ in range(3):
    target_position = random.choice(positions)
    target_object = random.choice(objects)
    objects.remove(target_object)
    
    distractor_objects = random.sample(objects, 2)
    distractor_positions = random.sample(positions, 2)
    
    row = {
        'target position': target_position,
        'target object': target_object,
        'distractor object position 1': distractor_positions[0],
        'distractor object 1': distractor_objects[0],
        'distractor object position 2': distractor_positions[1],
        'distractor object 2': distractor_objects[1],
        
    }
    new_data.append(row)

random.shuffle(new_data)
# Create DataFrame from the new data
new_df = pd.DataFrame(new_data)

# Save the new DataFrame to a CSV file
new_df.to_csv('new_file.csv', index=False)
