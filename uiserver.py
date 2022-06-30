from colorama import *
from websockets import serve, exceptions, basic_auth_protocol_factory
from threading import Thread
import asyncio as aio
import random
import json
import os
import re

class Game:

	def __init__(self, player1, player2):
		self.players = [player1, player2]
		self.result = None
		self.fleets = [None, None]
		self.shots = [None, None]
		self.next_move = [None, None]

	async def run(self):
		self.result = random.randint(0, 2)

	async def tryplace(self, player, fleet):
		pass

	async def tryshoot(self, player, x, y):
		pass

	def forfeit(self, player):
		pass

class User:

	def __init__(self, username, password, score):
		self.username = username
		self.password = password
		self.score = score
		self.websocket = None
		self.searching = False
		self.game = None

	def save_to_dict(self):
		return {
			'username': self.username,
			'password': self.password,
			'score': self.score
		}

	def get_total_score(self):
		return sum(self.score.values())

	def switch(self, searching, game):
		if self.game:
			self.game.forfeit(self)
		self.searching = searching
		self.game = game

	def kick(self):
		self.switch(False, None)
		if self.websocket:
			self.websocket.close()

	async def trysend(self, message):
		try:
			await self.websocket.send(message)
		except exceptions.WebSocketException:
			self.kick()

class UIServer():

	def __init__(self):
		self.load_data()
		self.games = []
		self.view = None
		self.running = True
		self.frozen = False
		self.pairing = False
		self.pairing_interval = 10
		self.score_weight = 0.1
		self.rank_scale = 7000
		self.rank_offset = 3000

	def load_data(self):
		self.users = {}
		try:
			with open('userdata.json', 'r') as f:
				data = json.load(f)
			for username in data:
				self.users[username] = User(*data[username].values())
		except FileNotFoundError:
			pass

	def save_data(self):
		data = {}
		for user in self.users.values():
			data[user.username] = user.save_to_dict()
		with open('userdata.json', 'w') as f:
			json.dump(data, f, indent=4)
			
	def player_ranking(self, player):
		return round(self.rank_offset + player.get_total_score() / len(self.users) * self.rank_scale)
	
	def ranking_string(self, n, width):
		s = "["
		for k in range(width):
			if n > (k*(self.rank_scale+self.rank_offset)/width):
				s += "#"
			else:
				s += " "
		s += "] "
		s += str(n)
		s += "/"
		s += str(self.rank_scale+self.rank_offset)
		s += '\n'
		return s

	def print(self):
		terminal_size = os.get_terminal_size()
		sx, sy = terminal_size.columns, terminal_size.lines
		title = 'Battleship Server'
		s = ''
		s += f"\n{' ' * ((sx - len(title)) // 2)}{title}\n\n"
		s += 'Users\n'
		for user in self.users.values():
			s += Fore.GREEN
			if user.websocket:
				s += Style.DIM
			else:
				s += Style.NORMAL
			s += " " + user.username
			s += (14 - len(user.username)) * " "
			s += self.ranking_string(self.player_ranking(user), sx - 28)
			s += Style.RESET_ALL
		s += '\n' * (sy - 6 - len(self.users))
		s += 'pairing: '
		s += 'on' if self.pairing else 'off'
		s += '\n'
		if self.frozen and self.running:
			s += '>>> '
		print(s, end='')

	async def authenticate(self, username, password):
		hex_password = password.encode().hex()
		if username in self.users:
			if not self.users[username].websocket:
				if self.users[username].password is None:
					if re.fullmatch(r'\w{3,13}', password):
						self.users[username].password = hex_password
						return True
				elif self.users[username].password == hex_password:
					return True
		return False

	async def connect(self, websocket):
		user = self.users[websocket.username]
		user.websocket = websocket
		try:
			async for msg in websocket:
				if msg == 'idle':
					user.switch(False, None)
				elif msg == 'search':
					user.switch(True, None)
				elif m := re.fullmatch(r'place (.+)', msg):
					if user.game:
						await user.game.tryplace(user, m.group(1))
					else:
						await websocket.send('no')
				elif m := re.fullmatch(r'shoot (\d+),(\d+)', msg):
					if user.game:
						await user.game.tryshoot(user, int(m.group(1)), int(m.group(2)))
					else:
						await websocket.send('no')
				else:
					await websocket.send('no')
				await aio.sleep(0.1)
		except exceptions.WebSocketException:
			return
		finally:
			user.switch(False, None)
			user.websocket = None

	async def pair(self, player1, player2):
		game = Game(player1, player2)
		player1.switch(False, game)
		player2.switch(False, game)
		self.games.append(game)
		await game.run()
		player1.score[player2.username] *= 1 - self.score_weight
		player1.score[player2.username] += self.score_weight * game.result
		player2.score[player1.username] = 1 - player1.score[player2.username]
		self.games.remove(game)

	async def pair_players(self):
		while True:
			if self.pairing:
				players = list(filter(lambda user: user.searching, self.users.values()))
				if len(players) > 1:
					aio.create_task(self.pair(*random.sample(players, 2)))
			await aio.sleep(self.pairing_interval)

	async def command(self, cmd):
		if cmd == '' or not self.frozen:
			self.frozen = True
		elif cmd == 'a':
			self.frozen = False
		elif cmd == 'q':
			self.running = False
		elif m := re.fullmatch(r'register (\w{3,13})', cmd):
			username = m.group(1)
			if not username in self.users:
				self.users[username] = User(username, None, {})
				for username2 in self.users:
					self.users[username].score[username2] = 0.5
					self.users[username2].score[username] = 0.5
		elif m := re.fullmatch(r'unregister (\w{3,13})', cmd):
			username = m.group(1)
			if username in self.users:
				self.users[username].kick()
				self.users.pop(username)
				for username2 in self.users:
					self.users[username2].score.pop(username)
		elif m := re.fullmatch(r'resetpassword (\w{3,13})', cmd):
			username = m.group(1)
			if username in self.users:
				self.users[username].password = None
		elif m := re.fullmatch(r'kick (\w{3,13})', cmd):
			username = m.group(1)
			if username in self.users:
				self.users[username].kick()
		elif cmd == 'pairing on':
			self.pairing = True
		elif cmd == 'pairing off':
			self.pairing = False

	async def ainput(self):
		loop = aio.get_running_loop()
		future = loop.create_future()
		function = lambda: loop.call_soon_threadsafe(future.set_result, input())
		Thread(target=function, daemon=True).start()
		return await future

	async def draw(self, interval):
		while True:
			if not self.frozen:
				self.print()
			await aio.sleep(interval)

	async def main(self, host, port, fps):
		try:
			aio.create_task(self.draw(1 / fps))
			aio.create_task(self.pair_players())
			protocol = basic_auth_protocol_factory(check_credentials=self.authenticate)
			async with serve(self.connect, host, port, create_protocol=protocol):
				while self.running:
					await self.command(await self.ainput())
					self.print()
		finally:
			self.save_data()

if __name__ == '__main__':
	try:
		aio.run(UIServer().main(None, 1234, 5))
	except KeyboardInterrupt:
		print()