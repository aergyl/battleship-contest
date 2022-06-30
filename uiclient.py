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

async def fixed_connect(host, port):
	loop = aio.get_running_loop()
	reader = aio.StreamReader()
	protocol = aio.StreamReaderProtocol(reader)
	transport, _ = await loop.create_connection(lambda: protocol, host, port)
	transport.set_write_buffer_limit(0)
	writer = aio.StreamWriter(transport, protocol, reader, loop)
	return reader, writer

async def ainput():
		loop = aio.get_running_loop()
		future = loop.create_future()
		function = lambda: loop.call_soon_threadsafe(future.set_result, input())
		Thread(target=function, daemon=True).start()
		return await future


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

	async def main(self):
		reader, writer = await fixed_connect(HOST, PORT)
		
			aio.create_task(self.listen())
			while True:
				#self.print()
				#await self.command(await self.ainput())
				await ws.send('search')
				await aio.sleep(0.1)

if __name__ == '__main__':
	try:
		if not USERNAME:
			USERNAME = input('Username: ')
		if not PASSWORD:
			PASSWORD = getpass()
		aio.run(UIClient().main())
	except KeyboardInterrupt:
		print()
