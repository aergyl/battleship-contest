from random import randint

def start_new_game(opponent, player_number):
	pass

def build_fleet():
	return [
		(1, 1, 'H'),
		(4, 1, 'H'),
		(1, 3, 'V'),
		(3, 3, 'H'),
		(3, 5, 'H')
	]

def shoot():
	return randint(0, 9), randint(0, 9)

def oppshot(x, y):
	pass

def hit_or_miss(result):
	pass

def game_over(result):
	pass

############################################################

HOST = 'localhost'
PORT = 1234

USERNAME = ''
PASSWORD = ''

############################################################
from colorama import *
from threading import Thread
from getpass import getpass
import asyncio as aio
import os
import re

def safeinput():
	try:
		return input()
	except EOFError:
		return ''

async def ainput():
	loop = aio.get_running_loop()
	future = loop.create_future()
	function = lambda: loop.call_soon_threadsafe(future.set_result, safeinput())
	Thread(target=function, daemon=True).start()
	return await future

async def trysend(stream, message):
	try:
		data = (message + '\n').encode()
		await stream.drain()
		stream.write(data)
		await stream.drain()
		return True
	except OSError:
		return False

async def tryrecv(stream):
	try:
		data = await stream.readline()
		message = data.decode().strip()
		return message
	except ValueError:
		return ''

class UIClient:

	def __init__(self):
		self.playing = False
		self.opponent = None
		self.number = None
		self.idx = None
		self.reset_shots()
		init()

	def reset_shots(self):
		self.shot = (0, 0)
		self.shots = [[], []]
		for k in range(2):
			for _ in range(10):
				self.shots[k].append([None] * 10)

	def print(self):
		terminal_size = os.get_terminal_size()
		sx, sy = terminal_size.columns, terminal_size.lines
		s = '\n' * (sy // 2 - 10)
		for k in range(2):
			for y in range(10):
				s += ' ' * (sx // 2 - 10)
				for x in range(10):
					if not self.shots[k][x][y]:
						s += Back.BLACK
					elif self.shots[k][x][y] == 'hit':
						s += Back.YELLOW
					elif self.shots[k][x][y] == 'miss':
						s += Back.BLUE
					elif self.shots[k][x][y] == 'end':
						s += Back.RED
					s += '  '
				s += Back.RESET + '\n'
			s += '\n\n\n'
		s += '\n' * (sy // 2 - 10)
		if not self.playing:
			s += '>>> '
		print(s, end='')

	async def listen(self):
		while True:
			message = await tryrecv(self.reader)
			if message in ('', 'kick'):
				break
			elif m := re.fullmatch(r'new (.+?) ([12])', message):
				self.playing = True
				self.reset_shots()
				self.opponent, self.number = m.group(1), int(m.group(2))
				self.idx = self.number - 1
				start_new_game(self.opponent, self.number)
			elif message == 'build':
				fleet = build_fleet()
				await trysend(self.writer, 'build ' + ' '.join(f"{x},{y},{d}" for x, y, d in fleet))
			elif message == 'shoot':
				self.shot = shoot()
				self.idx = 1 - self.idx
				await trysend(self.writer, f"shoot {self.shot[0]} {self.shot[1]}")
			elif m := re.fullmatch(r'oppshot (\d) (\d)', message):
				self.shot = (int(m.group(1)), int(m.group(2)))
				self.idx = 1 - self.idx
				oppshot(*self.shot)
			elif message in ('hit', 'miss', 'end'):
				self.shots[self.idx][self.shot[0]][self.shot[1]] = message
				hit_or_miss(message)
				self.print()
			elif message in ('lost', 'won', 'tie'):
				self.playing = False
				game_over(message)

	async def command(self):
		while True:
			self.print()
			cmd = await ainput()
			if cmd == '':
				self.playing = False
				self.reset_shots()
				await trysend(self.writer, 'idle')
			elif self.playing:
				pass
			elif cmd == 'search':
				await trysend(self.writer, 'search')
			elif cmd == 'test':
				await trysend(self.writer, 'test')

	async def main(self):
		self.reader, self.writer = await aio.open_connection(HOST, PORT)
		global USERNAME, PASSWORD
		if not USERNAME:
			USERNAME = input('Username: ')
		if not PASSWORD:
			PASSWORD = getpass()
		await trysend(self.writer, USERNAME)
		await trysend(self.writer, PASSWORD)
		if await tryrecv(self.reader) == 'ok':
			aio.create_task(self.command())
			await self.listen()
		else:
			print('Authentication failed')
		self.writer.close()

if __name__ == '__main__':
	try:
		aio.run(UIClient().main())
	except KeyboardInterrupt:
		print('\033[A')
	except OSError:
		print('Connection failed.')