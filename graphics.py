from colorama import init, Fore, Back, Style

init()

FG_COLORS = {
	's': Fore.BLACK,
	'r': Fore.RED,
	'g': Fore.GREEN,
	'y': Fore.YELLOW,
	'b': Fore.BLUE,
	'm': Fore.MAGENTA,
	'c': Fore.CYAN,
	'w': Fore.WHITE
}

BG_COLORS = {
	's': Back.BLACK,
	'r': Back.RED,
	'g': Back.GREEN,
	'y': Back.YELLOW,
	'b': Back.BLUE,
	'm': Back.MAGENTA,
	'c': Back.CYAN,
	'w': Back.WHITE
}

STYLE = {
	'd': Style.DIM,
	'n': Style.NORMAL,
	'l': Style.BRIGHT
}

def fg(string, color):
	return FG_COLORS[color] + string + Fore.RESET

def bg(string, color):
	return BG_COLORS[color] + string + Back.RESET

def fbs(string, x):
	return FG_COLORS[x[0]] + BG_COLORS[x[1]] + STYLE[x[2]] + string + Style.RESET_ALL