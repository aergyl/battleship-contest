import asyncio
from websockets import serve, exceptions
import random
from constants import *
from ship import Ship
from fleet import Fleet

class Player:
    def __init__(self, name, websocket):
        self.name = name
        self.websocket = websocket
    
    # Let player build fleet
    async def new_game(self, opp, pnum):
        await self.websocket.send("play " + opp.name)
        await self.websocket.send(str(pnum))
        fleet = Fleet()
        for i in range(sum(FLEET_DIM.values())):
            row1, col1, row2, col2 = map(int, (await self.websocket.recv()).split())
            fleet.add_ship(Ship(col1, row1, col2, row2))  # assuming pos x = down
        if(not fleet.validate()):
            self.websocket.send("invalid")
            return None
        fleet.setup()
        await self.websocket.send("ok")
        return fleet

players = []

async def play_games():
    while 1:
        if(len(players) < 2):
            print("Too few players")
            await asyncio.sleep(5)
            continue
        p = [None] + random.sample(players, 2)  # 1-indexerad
        print(f"{p[1].name} vs {p[2].name}")
        task1 = asyncio.create_task(p[1].new_game(p[2], 1))
        task2 = asyncio.create_task(p[2].new_game(p[1], 2))
        fleets = [None, await task1, await task2]  # 1-indexerad
        # todo kolla om någon fleet är None
        print("Fleets constructed")
        turn = 1
        while 1:
            print("Waiting for player", turn)
            row, col = map(int, (await p[turn].websocket.recv()).split())
            print(turn, "shoots at", row, col)
            r = fleets[turn^3].get_hit_by(col, row)  # assuming pos x = down
            await p[turn^3].websocket.send(f"{row} {col}")
            if(r == SIGNAL_MISS):
                await p[turn].websocket.send("miss")
            elif(r == SIGNAL_HIT):
                await p[turn].websocket.send("hit")
            elif(r == SIGNAL_SUNK):
                await p[turn].websocket.send("sunk")
            elif(r == SIGNAL_LOST):
                await p[turn].websocket.send("win")
                await p[turn^3].websocket.send("lost")
                return
            turn = turn^3

async def connect(websocket):
    name = None
    try:
        name = await websocket.recv()
        #todo kolla om namnet redan är taget, innehåller mellanslag, är för långt osv
        print(name, "connected")
        user = Player(name, websocket)
        players.append(user)
        await websocket.send("ok")
        await asyncio.Future()
    except (exceptions.ConnectionClosedError, exceptions.ConnectionClosedOK):
        pass
    # todo ta bort spelaren ur players

async def main():
    asyncio.create_task(play_games())
    async with serve(connect, "0.0.0.0", 1234, ping_interval=None):
        await asyncio.Future()

asyncio.run(main())