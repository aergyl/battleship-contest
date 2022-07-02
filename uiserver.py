from fleet import Fleet
from colorama import *
from threading import Thread
import asyncio as aio
import random
import json
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

class Bot:

	def __init__(self, game):
		self.username = '<BOT>'
		self.game = game

	async def send(self, message):
		if message == 'build':
			await self.game.trybuild(self, '1,1,H 4,1,H 1,3,V 3,3,H 3,5,H')
		elif message == 'shoot':
			await self.game.tryshoot(self, random.randrange(10), random.randrange(10))

class Game:

	TIMELIMIT_BUILD = 2
	TIMELIMIT_SHOOT = 0.5

	def __init__(self, player1, player2=None):
		if player2 is None:
			player2 = Bot(self)
		self.players = [player1, player2]
		self.fleets = [None, None]
		self.next_move = [None, None]
		self.result = None

	async def run(self):
		for i in range(2):
			await self.players[i].send(f"new {self.players[1 - i].username} {i + 1}")
		for i in range(2):
			await self.players[i].send('build')
		await aio.sleep(self.TIMELIMIT_BUILD)
		if not any(self.next_move):
			self.result = 0.5
		elif not self.next_move[0]:
			self.result = 0
		elif not self.next_move[1]:
			self.result = 1
		fleets = tuple(self.next_move)
		gturn = 1
		pturn = 0
		while self.result is None:
			self.next_move[pturn] = None
			await self.players[pturn].send('shoot')
			await aio.sleep(self.TIMELIMIT_SHOOT)
			if self.result is not None:
				break
			if self.next_move[pturn] is None:
				self.result = pturn
				break
			x, y = self.next_move[pturn]
			await self.players[1 - pturn].send(f"oppshot {x} {y}")
			r = fleets[1 - pturn].get_hit_by(x, y)
			await self.players[pturn].send(r)
			await self.players[1 - pturn].send(r)
			if r == 'end':
				self.result = 1 - pturn
				break
			pturn = 1 - pturn
			if pturn == 0:
				gturn += 1
			if gturn > 1000:
				self.result = 0.5
		if self.result == 0:
			await self.players[0].send('lost')
			await self.players[1].send('won')
		elif self.result == 1:
			await self.players[1].send('lost')
			await self.players[0].send('won')
		else:
			await self.players[0].send('tie')
			await self.players[1].send('tie')

	async def trybuild(self, player, fleet_string):
		idx = self.players.index(player)
		if self.next_move[idx]:
			return
		fleet = Fleet()
		for string, size in zip(fleet_string.split(), (2, 3, 3, 4, 5)):
			if m := re.fullmatch(r'(\d),(\d),([HV])', string):
				x, y, d = int(m.group(1)), int(m.group(2)), int(m.group(3) == 'H')
				x2 = x + (size - 1) * d
				y2 = y + (size - 1) * (1 - d)
				fleet.add_ship(x, y, x2, y2)
		if fleet.validate():
			fleet.setup()
			self.next_move[idx] = fleet

	async def tryshoot(self, player, x, y):
		idx = self.players.index(player)
		if self.next_move[idx] is None:
			self.next_move[idx] = (x, y)

	def forfeit(self, player):
		if self.result is None:
			self.result = self.players.index(player)

class User:

	UNREAD_LIMIT = 10

	def __init__(self, username, password, score):
		self.username = username
		self.password = password
		self.score = score
		self.searching = False
		self.game = None
		self.writer = None
		self.listener = None
		self.unread = []

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

	async def kick(self):
		if self.listener:
			self.listener.cancel()
			await self.send('kick')

	async def send(self, message):
		if self.writer:
			for task in self.unread:
				if task.done():
					self.unread.remove(task)
			self.unread.append(aio.create_task(trysend(self.writer, message)))
			if len(self.unread) > self.UNREAD_LIMIT:
				await self.kick()

class UIServer():

	HOST = None
	PORT = 1234

	FPS = 5
	PAIR_INTERVAL = 1
	LISTEN_PAUSE = 0.1

	RANK_SCALE = 7000
	RANK_OFFSET = 3000

	DATAPATH = 'userdata.json'

	def __init__(self):
		self.load_data()
		self.games = []
		self.running = True
		self.frozen = False
		self.pairing = False
		self.score_weight = 0.0

	def load_data(self):
		self.users = {}
		try:
			with open(self.DATAPATH, 'r') as f:
				data = json.load(f)
			for username in data:
				self.users[username] = User(*data[username].values())
		except FileNotFoundError:
			pass

	def save_data(self):
		data = {}
		for user in self.users.values():
			data[user.username] = user.save_to_dict()
		with open(self.DATAPATH, 'w') as f:
			json.dump(data, f, indent=4)
			
	def player_ranking(self, player):
		return round(self.RANK_OFFSET + player.get_total_score() / len(self.users) * self.RANK_SCALE)
	
	def ranking_string(self, n, width):
		s = "["
		for k in range(width):
			if n > (k * (self.RANK_SCALE + self.RANK_OFFSET) / width):
				s += "#"
			else:
				s += " "
		s += "] "
		s += str(n)
		s += "/"
		s += str(self.RANK_SCALE + self.RANK_OFFSET)
		s += '\n'
		return s

	def print(self):
		terminal_size = os.get_terminal_size()
		sx, sy = terminal_size.columns, terminal_size.lines
		title = 'Battleship Leaderboard'
		s = ''
		if self.pairing:
			s += Fore.MAGENTA
		else:
			s += Fore.CYAN
		s += f"\n{' ' * ((sx - len(title)) // 2)}{title}\n\n"
		for user in self.users.values():
			if user.writer:
				if user.searching:
					s += Fore.YELLOW
				elif user.game:
					if user.game.result is None:
						s += Fore.GREEN
					else:
						s += Fore.BLUE
				else:
					s += Fore.WHITE
			else:
				s += Fore.RED
			s += ' ' + user.username
			s += (14 - len(user.username)) * ' '
			s += self.ranking_string(self.player_ranking(user), sx - 28)
			s += Style.RESET_ALL
		s += '\n' * (sy - 5 - len(self.users))
		s += str(self.score_weight) + '\n'
		if self.frozen and self.running:
			s += '>>> '
		print(s, end='')

	def authenticate(self, username, password):
		hex_password = password.encode().hex()
		if username in self.users:
			if not self.users[username].writer:
				if self.users[username].password is None:
					if re.fullmatch(r'\w{3,13}', password):
						self.users[username].password = hex_password
						return True
				elif self.users[username].password == hex_password:
					return True
		return False

	async def listen(self, reader, user):
		try:
			while True:
				message = await tryrecv(reader)
				if message == '':
					break
				elif message == 'idle':
					user.switch(False, None)
				elif message == 'search':
					user.switch(True, None)
				elif message == 'test':
					aio.create_task(self.run_test(user))
				elif m := re.fullmatch(r'build (.+)', message):
					if user.game:
						await user.game.trybuild(user, m.group(1))
				elif m := re.fullmatch(r'shoot (\d+) (\d+)', message):
					if user.game:
						await user.game.tryshoot(user, int(m.group(1)), int(m.group(2)))
				await aio.sleep(self.LISTEN_PAUSE)
		except aio.CancelledError:
			return

	async def connect(self, reader, writer):
		user = None
		try:
			username = await tryrecv(reader)
			password = await tryrecv(reader)
			if self.authenticate(username, password):
				user = self.users[username]
				user.writer = writer
				await user.send('ok')
				user.listener = aio.create_task(self.listen(reader, user))
				await user.listener
		except KeyboardInterrupt as e:
			raise e
		except:
			return
		finally:
			if user:
				user.listener = None
				user.switch(False, None)
				user.unread.clear()
				user.writer = None
			writer.close()

	async def run_test(self, player):
		game = Game(player)
		self.games.append(game)
		player.switch(False, game)
		await game.run()
		self.games.remove(game)

	async def run_game(self, player1, player2):
		game = Game(player1, player2)
		self.games.append(game)
		player1.switch(False, game)
		player2.switch(False, game)
		await game.run()
		if game.result == 1:
			score = 1
		elif game.result == 2:
			score = 0
		else:
			score = 0.5
		player1.score[player2.username] *= 1 - self.score_weight
		player1.score[player2.username] += self.score_weight * score
		player2.score[player1.username] = 1 - player1.score[player2.username]
		self.games.remove(game)

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
				await self.users[username].kick()
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
				await self.users[username].kick()
		elif cmd == 'pairing on':
			self.pairing = True
		elif cmd == 'pairing off':
			self.pairing = False
		elif m := re.fullmatch(r'weight (0\.\d)', cmd):
			self.score_weight = float(m.group(1))

	async def pair(self, interval):
		while True:
			if self.pairing:
				players = list(filter(lambda user: user.searching, self.users.values()))
				if len(players) > 2:
					aio.create_task(self.run_game(*random.sample(players, 2)))
			await aio.sleep(interval)

	async def draw(self, interval):
		while True:
			if not self.frozen:
				self.print()
			await aio.sleep(interval)

	async def main(self):
		try:
			aio.create_task(self.draw(1 / self.FPS))
			aio.create_task(self.pair(self.PAIR_INTERVAL))
			async with await aio.start_server(self.connect, self.HOST, self.PORT):
				while self.running:
					await self.command(await ainput())
					self.print()
		finally:
			self.save_data()

if __name__ == '__main__':
	try:
		aio.run(UIServer().main())
	except KeyboardInterrupt:
		print('\033[A')
