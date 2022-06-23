from graphics import fg, bg, fbs
from websockets import serve, exceptions, basic_auth_protocol_factory
from threading import Thread
import asyncio as aio
import json
import os
import re

class Game:

	count = 0

	def __init__(self, player1, player2):
		self.players = [player1, player2]
		self.running = True
		self.won = None
		self.fleets = [None, None]
		self.shots = [None, None]
		self.next_move = [None, None]
		self.spectators = []
		self.id = self.count
		self.count += 1
		self.count %= 1000

	async def run(self):
		pass

	async def tryplace(self, player, fleet):
		pass

	async def tryshoot(self, player, x, y):
		pass

class Client:

	def __init__(self, ws):
		self.ws = ws
		self.name = ws.username
		self.playing = False
		self.game = None

	def switch(self, playing, game):
		if self.game:
			if self.playing:
				self.game.players.replace(self, None)
			else:
				self.game.spectators.remove(self)
		self.playing = playing
		self.game = game

class UIServer():

	def __init__(self):
		self.userdata = {}
		self.clients = []
		self.games = []
		self.running = True
		self.frozen = False

	def load_data(self):
		with open('userdata.json', 'r') as f:
			self.userdata = json.load(f)

	def save_data(self):
		with open('userdata.json', 'w') as f:
			json.dump(self.userdata, f, indent=4)

	def print(self):
		os.system('clear||cls')
		terminal_size = os.get_terminal_size()
		sx, sy = terminal_size.columns, terminal_size.lines
		title = 'Battleship Server'
		s = ''
		s += f"\n{' ' * ((sx - len(title)) // 2)}{fg(title, 'g')}\n\n"
		s += fg(' Active Users\n', 'c')
		for client in self.clients:
			s += f" {fg(client.name, 'm')}\n"
		s += '\n' * (sy - 6 - len(self.clients))
		if self.frozen and self.running:
			s += '>>> '
		print(s, end='')

	async def authenticate(self, username, password):
		if username in self.userdata:
			if self.userdata[username]['password'] is None:
				if re.fullmatch(r'\w{3,13}', password):
					self.userdata[username]['password'] = password
					return True
				else:
					return False
			elif self.userdata[username]['password'] == password:
				return True
		else:
			return False

	async def connect(self, ws):
		client = Client(ws)
		self.clients.append(client)
		try:
			async for msg in ws:
				if msg == 'idle':
					client.switch(False, None)
				elif msg == 'play':
					client.switch(True, None)
				elif msg == 'spectate':
					client.switch(False, None)
					await ws.send(' '.join(f"{g.id},{','.join(g.players)}" for g in self.games))
				elif m := re.fullmatch(r'spectate (\d+)', msg):
					client.switch(False, None)
					for game in self.games:
						if game.id == int(m.group(1)):
							client.switch(False, game)
							game.spectators.append(client)
							break
					if not client.game:
						await ws.send('no')
				elif m := re.fullmatch(r'place (.+)', msg):
					if client.game and client.playing:
						await client.game.tryplace(client, m.group(1))
					else:
						await ws.send('no')
				elif m := re.fullmatch(r'shoot (\d+),(\d+)', msg):
					if client.game and client.playing:
						await game.tryshoot(client, int(m.group(1)), int(m.group(2)))
					else:
						await ws.send('no')
				else:
					await ws.send('no')
				await aio.sleep(0.1)
		except exceptions.WebSocketException:
			return
		finally:
			client.switch(False, None)
			self.clients.remove(client)

	async def command(self, cmd):
		if cmd == '' or not self.frozen:
			self.frozen = True
		elif cmd == 'a':
			self.frozen = False
		elif cmd == 'q':
			self.running = False
		elif m := re.fullmatch(r'register (\w{3,13})', cmd):
			username = m.group(1)
			if not username in self.userdata:
				self.userdata[username] = {
					'id': len(self.userdata) + 1,
					'score': 0,
					'password': None,
				}
		elif m := re.fullmatch(r'unregister (\w{3,13})', cmd):
			username = m.group(1)
			if username in self.userdata:
				self.userdata.pop(username)
			for client in self.clients:
				if client.name == username:
					client.close()

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

	async def main(self, port, fps):
		aio.create_task(self.draw(1 / fps))
		protocol = basic_auth_protocol_factory(check_credentials=self.authenticate)
		async with serve(self.connect, 'localhost', port, create_protocol=protocol):
			while self.running:
				await self.command(await self.ainput())
				self.print()

if __name__ == '__main__':
	try:
		server = UIServer()
		server.load_data()
		aio.run(server.main(1234, 5))
	except KeyboardInterrupt:
		print()
	finally:
		server.save_data()