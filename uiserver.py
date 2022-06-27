from colorama import *
from websockets import serve, exceptions, basic_auth_protocol_factory
from threading import Thread
from random import randrange
import asyncio as aio
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
		pass

	async def tryplace(self, player, fleet):
		pass

	async def tryshoot(self, player, x, y):
		pass

	def forfeit(self, player):
		pass

class User(dict):

	def __init__(self, username, password, score):
		self.username = username
		self.password = password
		self.score = score
		self.ws = None
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
		if self.ws:
			self.ws.close()

	async def trysend(self, message):
		try:
			await self.ws.send(message)
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
			json.dump(data, f)
			
	def player_ranking(player):
		return(round(rank_offset + player.get_total_score()*rank_scale))
	
	def ranking_string(n):
		s = "["
		s += Back.BLUE
		for k in range(100):
			if n > (k*(rank_scale+rank_offset)/100):
				s += " "
			else:
				s +=Back.RESET
				s += " "
		s += Back.RESET
		s += "] "
		s += str(n)
		s += "/"
		s += str(rank_scale+rank_offset)

	def print(self):
		terminal_size = os.get_terminal_size()
		sx, sy = terminal_size.columns, terminal_size.lines
		title = 'Battleship Server'
		s = ''
		s += f"\n{' ' * ((sx - len(title)) // 2)}{title}\n\n"
		s += 'Active Users\n'
		for user in self.users.values():
			if user.ws:
				s += Fore.GREEN
			else:
				s += Fore.RED
			s += f" {user.username} {user.get_total_score():.1f}\n"
			s += (20-len(user.username)) * " "
			s += ranking_string(player_ranking(user))
			s += Fore.RESET
		s += '\n' * (sy - 5 - len(self.users))
		if self.frozen and self.running:
			s += '>>> '
		print(s, end='')

	async def authenticate(self, username, password):
		hex_password = password.encode().hex()
		if username in self.users:
			if not self.users[username].ws:
				if self.users[username].password is None:
					if re.fullmatch(r'\w{3,13}', password):
						self.users[username].password = hex_password
						return True
				elif self.users[username].password == hex_password:
					return True
		return False

	async def connect(self, ws):
		user = self.users[ws.username]
		user.ws = ws
		try:
			async for msg in ws:
				if msg == 'idle':
					user.switch(False, None)
				elif msg == 'search':
					user.switch(True, None)
				elif m := re.fullmatch(r'place (.+)', msg):
					if user.game:
						await user.game.tryplace(user, m.group(1))
					else:
						await ws.send('no')
				elif m := re.fullmatch(r'shoot (\d+),(\d+)', msg):
					if user.game:
						await game.tryshoot(client, int(m.group(1)), int(m.group(2)))
					else:
						await ws.send('no')
				else:
					await ws.send('no')
				await aio.sleep(0.1)
		except exceptions.WebSocketException:
			return
		finally:
			user.switch(False, None)
			user.ws = None

	async def pair(self, player1, player2):
		game = Game(player1, player2)
		await game.run()
		old_score1 = player1.score[player2.username]
		old_score2 = player2.score[player1.username]
		if game.result == 0:
			score1 = score2 = 0.5
		elif game.result == 1:
			score1, score2 = 1, 0
		elif game.result == 2:
			score1, score2 = 0, 1
		player1.score[player2.username] = (1-score_weight)*old_score1 + score_weight*score1
		player2.score[player1.username] = (1-score_weight)*old_score2 + score_weight*score2

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
				for username2 in self.users:
					self.users[username2].score.pop(username)
				self.users.pop(username)
		elif m := re.fullmatch(r'resetpassword (\w{3,13})', cmd):
			username = m.group(1)
			if username in self.users:
				self.users[username].password = None
		elif m := re.fullmatch(r'kick (\w{3,13})', cmd):
			username = m.group(1)
			if username in self.users:
				self.users[username].kick()
		elif m == 'pairing on':
			self.pairing = True
		elif m == 'pairing off':
			self.pairing = False
					
	async def pair_players(self):
		while True:
			aio.sleep(pairing_interval)
			if pairing:
				available_players = list(filter(lambda client: client.playing, self.clients))
				if len(available_players) > 1:
					player_1 = available_players.pop(randrange(len(available_players)))
					player_2 = available_players.pop(randrange(len(available_players)))
					new_game = Game(player_1, player_2)
					self.games.append(new_game)
					aio.create_task(new_game.run())

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
