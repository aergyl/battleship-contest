############################################################

HOST = 'localhost'
PORT = 1234

USERNAME = 'Test'
PASSWORD = ''

############################################################
from colorama import *
from websockets import connect, exceptions
from threading import Thread
from getpass import getpass
import asyncio as aio
import os
import re

class UIClient:

	def __init__(self):
		init()

	def print(self):
		terminal_size = os.get_terminal_size()
		sx, sy = terminal_size.columns, terminal_size.lines
		s = ''
		s += f"\n{' ' * ((sx - len(USERNAME)) // 2)}{USERNAME}\n\n"
		s += '\n' * (sy - 5) + '>>> '
		print(s, end='')

	async def listen(self):
		async for msg in self.ws:
			pass

	async def command(self, cmd):
		if cmd == 'search':
			await self.ws.send('search')

	async def ainput(self):
		loop = aio.get_running_loop()
		future = loop.create_future()
		function = lambda: loop.call_soon_threadsafe(future.set_result, input())
		Thread(target=function, daemon=True).start()
		return await future

	async def main(self):
		async with connect(f"ws://{USERNAME}:{PASSWORD}@{HOST}:{PORT}") as ws:
			self.ws = ws
			aio.create_task(self.listen())
			while True:
				self.print()
				await self.command(await self.ainput())

if __name__ == '__main__':
	try:
		if not PASSWORD:
			PASSWORD = getpass()
		aio.run(UIClient().main())
	except KeyboardInterrupt:
		print()
	except (OSError, exceptions.WebSocketException):
		print('Connection failed.')