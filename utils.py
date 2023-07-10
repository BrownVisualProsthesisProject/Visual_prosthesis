from rapidfuzz import fuzz
import string
from Constants import LABELS

def find_closest_match(word):
	max_score = -1
	closest_match = None
	word_cleaned = word.translate(str.maketrans('', '', string.punctuation)).lower()
	print(word_cleaned)
	for key in LABELS:
		score = fuzz.ratio(word_cleaned, key)
		if score > .6 and score > max_score :
			max_score = score
			closest_match = key

	return closest_match
	
def depth_to_feet(mm):
	feet = mm / 304.8
	return round(feet, 1)

def calculate_distance(x_object, y_object, x_shape, y_shape):
	# Divide the frame into 9 sections
	section_width = x_shape // 3
	section_height = y_shape // 3

	# Determine the section in which the object is located
	section_x = (x_object*x_shape) // section_width
	section_y = (max(y_object-.15,0.0)*y_shape) // section_height
	
	print("sector x",section_x,"sector y", section_y)
	# Map the section to a movement direction
	if section_x == 0 and section_y == 0:
		direction = 'up left'
	elif section_x == 0 and section_y == 1:
		direction = 'left'
	elif section_x == 0 and section_y == 2:
		direction = 'down left'
	elif section_x == 1 and section_y == 0:
		direction = 'up'
	elif section_x == 1 and section_y == 1:
		direction = 'in front of you'
	elif section_x == 1 and section_y == 2:
		direction = 'down'
	elif section_x == 2 and section_y == 0:
		direction = 'up right'
	elif section_x == 2 and section_y == 1:
		direction = 'right'
	elif section_x == 2 and section_y == 2:
		direction = 'down right'
	
	return direction