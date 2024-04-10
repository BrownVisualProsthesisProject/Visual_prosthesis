import pandas as pd
import random

def gen_distractor_pos(target_pos, positions, far=True):
    if not far:
        valid_positions = [pos for pos in positions if abs(pos - target_pos) >= 2]
        return random.sample(valid_positions, 2)
    else:
        valid_positions = [pos for pos in positions if abs(pos - target_pos) >= 1]
        return random.sample(valid_positions, 2)

    #return random.sample(positions[:target_pos] + positions[target_pos+1:], 2)

far = False

# Read the original CSV file
df = pd.read_csv('labels_objects.csv')

# Filter rows where distance is not "far"
if not far:
    df = df[df['distance'] != 'far']
else:
    df = df[df['distance'] != 'near']

original_df = df.copy()
# Extract the labels and objects columns
objects = df['labels'].tolist()
#objects = df['object_name'].tolist()

# Create lists for target and distractor positions
positions = list(range(1, 8))

# Shuffle the objects to ensure randomness
random.shuffle(objects)

# Create a DataFrame for the new CSV
new_data = []

# Fill the first 7 rows with target and distractor positions
for i in range(7):
    target_position = i+1
    target_object = random.choice(objects)

    aux_list = []
    for item in objects[:]:  # Iterate over a copy of the list
        # Check if the string starts with the given letter
        if item.startswith(target_object[0]):
            # Remove the string from the original list and append it to the new list
            objects.remove(item)
            aux_list.append(item)
    
    distractor_objects = random.sample(objects, 2)
    distractor_positions = gen_distractor_pos(i+1, positions, far)
    print(distractor_positions,target_position)
    row = {
        'target position': target_position,
        'target object': target_object,
        'distractor object position 1': distractor_positions[0],
        'distractor object 1': distractor_objects[0],
        'distractor object position 2': distractor_positions[1],
        'distractor object 2': distractor_objects[1],
    }
    new_data.append(row)
    objects+=aux_list
    print(len(objects))

# Fill the last 3 rows with random target positions and other columns filled similarly
for _ in range(3):
    target_position = random.choice(positions)
    target_object = random.choice(objects)

    aux_list = []
    for item in objects[:]:  # Iterate over a copy of the list
        # Check if the string starts with the given letter
        if item.startswith(target_object[0]):
            # Remove the string from the original list and append it to the new list
            objects.remove(item)
            aux_list.append(item)

    distractor_objects = random.sample(objects, 2)
    distractor_positions = gen_distractor_pos(target_position, positions, far)
    print(distractor_positions,target_position)
    row = {
        'target position': target_position,
        'target object': target_object,
        'distractor object position 1': distractor_positions[0],
        'distractor object 1': distractor_objects[0],
        'distractor object position 2': distractor_positions[1],
        'distractor object 2': distractor_objects[1],
        
    }
    new_data.append(row)
    objects+=aux_list
    print(len(objects))

random.shuffle(new_data)
# Create DataFrame from the new data
new_df = pd.DataFrame(new_data)

if far:
    # Save the new DataFrame to a CSV file
    new_df.to_csv('far_trials_file.csv', index=False)
else:
    new_df.to_csv('close_trials_file.csv', index=False)
