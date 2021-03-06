#A rectangle-shaped ship class with collision detection etc.
class Ship:

	#Creates a ship by specifying one of its diagonals from (x1, y1) to (x2, y2).
	def __init__(self, x1, y1, x2, y2):

		#Standardize the representation of the rectangle.
		self.rect_x = (min(x1, x2), max(x1, x2))
		self.rect_y = (min(y1, y2), max(y1, y2))

		#Standardize the representation of the dimensions.
		width = abs(x1 - x2) + 1
		height = abs(y1 - y2) + 1
		self.dim = (max(width, height), min(width, height))

	#Checks if the ship is fully contained within the game board.
	def validate_position(self):
		validation_x = 0 <= self.rect_x[0] and self.rect_x[1] < 10
		validation_y = 0 <= self.rect_y[0] and self.rect_y[1] < 10
		return validation_x and validation_y

	#Checks if the ship is adjacent to another ship (horizontally, vertically or diagonally).
	def validate_adjacent(self, other_ship):
		validation_x = self.rect_x[0] > other_ship.rect_x[1] + 1 or other_ship.rect_x[0] > self.rect_x[1] + 1
		validation_y = self.rect_y[0] > other_ship.rect_y[1] + 1 or other_ship.rect_y[0] > self.rect_y[1] + 1
		return validation_x or validation_y

	#This should be called before starting the game, but only after a successful validation.
	def setup(self):

		#Store all of the squares that the ship occupy, along with a boolean representing whether that part is alive or not.
		self.squares = {}
		for x in range(self.rect_x[0], self.rect_x[1] + 1):
			for y in range(self.rect_y[0], self.rect_y[1] + 1):
				self.squares[x, y] = True

	#Interacts with a shot targeting (x, y) and returns a string indicating what happened.
	def get_hit_by(self, x, y):
		if (x, y) in self.squares:
			self.squares[x, y] = False
			return 'hit'
		else:
			return 'miss'

	#Checks if there are non-hit squares on the ship.
	def is_alive(self):
		return any(self.squares.values())