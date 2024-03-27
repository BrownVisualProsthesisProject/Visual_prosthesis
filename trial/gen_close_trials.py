import pandas as pd
import random

def gen_distractor_pos(target_pos, positions):
    valid_positions = [pos for pos in positions if abs(pos - target_pos) >= 2]
    return random.sample(valid_positions, 2)

    #return random.sample(positions[:target_pos] + positions[target_pos+1:], 2)

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
    distractor_positions = gen_distractor_pos(i, positions)
    
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
    print(positions[:target_position-1] + positions[target_position:], target_position)
    
    distractor_objects = random.sample(objects, 2)
    distractor_positions = gen_distractor_pos(target_position-1, positions)
    
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
new_df.to_csv('close_trials_file.csv', index=False)
