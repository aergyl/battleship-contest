# The number of squares in the x-direction and the y-direction, respectively.
BOARD_DIM = (10, 10)

# The dimensions of the ships to be used together with their respective count.
# The dimensions must be written with the highest number first.
FLEET_DIM = {
	(2, 1): 1,
	(3, 1): 2,
	(4, 1): 1,
	(5, 1): 1
}

# This is one way of ensuring that the game eventually ends.
MAX_NUM_OF_SHOTS = 150

# If set to False, SIGNAL_SUNK will be replaced with SIGNAL_HIT.
ANNOUNCE_WHEN_SUNK = False

# Signals used for communication.
SIGNAL_MISS = 0
SIGNAL_HIT = 1
SIGNAL_SUNK = 2
SIGNAL_LOST = 3

# Time limit to place all ships (seconds)
TIMELIMIT_PLACE = 2
# Time limit for shooting (seconds)
TIMELIMIT_SHOOT = 0.5
