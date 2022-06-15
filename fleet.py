from constants import *
from ship import Ship

#A container class for ships.
class Fleet:

	#Creates an empty fleet.
	def __init__(self):
		self.ships = []

	#Adds a ship to the fleet.
	def add_ship(self, x1, y1, x2, y2):
		assert type(x1) == type(y1) == type(x2) == type(y2) == int
		self.ships.append(Ship(x1, y1, x2, y2))

	#Checks if the fleet follow all of the rules.
	def validate(self):
		if not self.validate_dim():
			return False
		for ship in self.ships:
			if not ship.validate_position():
				return False
		for i in range(len(self.ships)):
			for j in range(i + 1, len(self.ships)):
				if not self.ships[i].validate_adjacent(self.ships[j]):
					return False
		return True

	#Checks if the ships in the fleet are of the correct dimensions.
	def validate_dim(self):
		dim_count = {}
		for ship in self.ships:
			if ship.dim in dim_count:
				dim_count[ship.dim] += 1
			else:
				dim_count[ship.dim] = 1
		return dim_count == FLEET_DIM

	#This should be called before starting the game, but only after a successful validation.
	def setup(self):
		for ship in self.ships:
			ship.setup()

	#Interacts with a shot targeting (x, y) and returns a signal indicating what happened.
	def get_hit_by(self, x, y):
		assert type(x) == type(y) == int
		assert 0 <= x < BOARD_DIM[0] and 0 <= y < BOARD_DIM[1]
		for ship in self.ships:
			signal = ship.get_hit_by(x, y)
			if signal != SIGNAL_MISS:
				if self.is_alive():
					return signal
				else:
					return SIGNAL_LOST
		return SIGNAL_MISS

	#Checks if there are any ships alive in the fleet.
	def is_alive(self):
		return any(ship.is_alive() for ship in self.ships)