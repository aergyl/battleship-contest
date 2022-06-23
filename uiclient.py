from random import randint

USERNAME = 'Test'
PASSWORD = '' #Keep empty for prompt.

############################################################
from colorama import init, Fore, Back, Style
from websockets import connect, exceptions
from threading import Thread
from getpass import getpass
import asyncio as aio
import os
import re

class UIClient:

	def __init__(self):
		self.msg = '---'
		init()

	def print(self):
		os.system('clear||cls')
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
		pass

	async def ainput(self):
		loop = aio.get_running_loop()
		future = loop.create_future()
		function = lambda: loop.call_soon_threadsafe(future.set_result, input())
		Thread(target=function, daemon=True).start()
		return await future

	async def main(self, port):
		async with connect(f"ws://{USERNAME}:{PASSWORD}@localhost:{port}") as ws:
			self.ws = ws
			aio.create_task(self.listen())
			while True:
				self.print()
				await self.command(await self.ainput())

if __name__ == '__main__':
	try:
		if not PASSWORD:
			PASSWORD = getpass()
		aio.run(UIClient().main(1234))
	except KeyboardInterrupt:
		print()
	except (OSError, exceptions.WebSocketException):
		print('Connection failed.')