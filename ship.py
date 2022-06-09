
from game_constants import BOARD_DIM

#A rectangle-shaped ship class with collision detection etc.
class Ship:

	#Creates a ship by specifying one of its diagonals from (x1, y1) to (x2, y2).
	def __init__(self, x1, y1, x2, y2):
		self.width = abs(x1 - x2) + 1
		self.height = abs(y1 - y2) + 1

		#Standardize the representation of the dimensions.
		self.dim = (max(self.width, self.height), min(self.width, self.height))

		#Standardize the representation of the rectangle.
		self.x = (min(x1, x2), max(x1, x2))
		self.y = (min(y1, y2), max(y1, y2))

	#Checks if the ship is fully contained within the game board.
	def validate_position(self):
		validation_x = 0 < self.x[0] and self.x[1] < BOARD_DIM[0]
		validation_y = 0 < self.y[0] and self.y[1] < BOARD_DIM[1]
		if validation_x and validation_y:
			return True
		else:
			return False

	#Checks if the ship is adjacent to another ship (horizontally, vertically or diagonally).
	def validate_adjacent(self, other_ship):
		validation_x = self.x[0] > other_ship.x[1] + 1 or other_ship.x[0] > self.x[1] + 1
		validation_y = self.y[0] > other_ship.y[1] + 1 or other_ship.y[0] > self.y[1] + 1
		if validation_x or validation_y:
			return True
		else:
			return False

	#Checks if the ship is hit by a shot targeting (x, y).
	def is_hit_by(self, x, y):
		if (self.x[0] <= x <= self.x[0]) and (self.y[0] <= y <= self.y[0]):
			return True
		else:
			return False
