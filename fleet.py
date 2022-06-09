
from rules import FLEET_DIM

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
		for i in range(len(ships)):
			for j in range(i, len(ships)):
				if not ships[i].validate_adjacent(ships[j]):
					return False
		return True

	#Checks if the ships are of the correct dimensions.
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
		if count_dim == SHIPS_DIM:
			return True
		else:
			return False

	#Checks if any ship in the fleet is hit by a shot targeting (x, y).
	def is_hit_by(self, x, y):
		for ship in self.ships:
			if ship.is_hit_by(x, y):
				return True
		return False
