
from constants import *

#A container class for ships.
class Fleet:

	#Creates an empty fleet.
	def __init__(self):
		self.ships = []

	#Adds a ship to the fleet.
	def add_ship(self, ship):
		self.ships.append(ship)

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
		count_dim = {}
		for ship in self.ships:
			if ship.dim in FLEET_DIM:
				if ship.dim in count_dim:
					count_dim[ship.dim] += 1
				else:
					count_dim[ship.dim] = 1
			else:
				return False
		if count_dim == FLEET_DIM:
			return True
		else:
			return False

	#This should be called before starting the game, but only after a successful validation.
	def setup(self):
		for ship in self.ships:
			ship.setup()

	#Interacts with a shot targeting (x, y) and returns a signal indicating what happened.
	def get_hit_by(self, x, y):
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
		for ship in self.ships:
			if ship.is_alive():
				return True
		return False
