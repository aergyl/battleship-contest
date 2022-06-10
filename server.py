import asyncio
import traceback
from websockets import serve, exceptions
import random
from constants import *
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
            try:
                r = await asyncio.wait_for(self.websocket.recv(), timeout=1)
            except asyncio.TimeoutError:
                await self.websocket.send("timeout")
                return None
            try:
                row1, col1, row2, col2 = map(int, r.split())
                fleet.add_ship(col1, row1, col2, row2)  # assuming pos x = down
            except:
                await self.websocket.send("invalid ship")
                return None
        if(not fleet.validate()):
            self.websocket.send("invalid fleet")
            return None
        fleet.setup()
        return fleet

players = []

async def play_game(p):
    task1 = asyncio.create_task(p[1].new_game(p[2], 1))
    task2 = asyncio.create_task(p[2].new_game(p[1], 2))
    fleets = [None, await task1, await task2]  # 1-indexerad
    if(fleets[1] is None and fleets[2] is None): return 0
    if(fleets[1] is None): return 2
    if(fleets[2] is None): return 1
    await p[1].websocket.send("ok")
    await p[2].websocket.send("ok")
    turn = 1
    while 1:
        r = await p[turn].websocket.recv()
        row, col = map(int, r.split())
        r = fleets[turn^3].get_hit_by(col, row)  # assuming pos x = down
        await p[turn^3].websocket.send(f"{row} {col}")
        if(r == SIGNAL_MISS):
            await p[turn].websocket.send("miss")
            await p[turn^3].websocket.send("miss")
        elif(r == SIGNAL_HIT):
            await p[turn].websocket.send("hit")
            await p[turn^3].websocket.send("hit")
        elif(r == SIGNAL_SUNK):
            await p[turn].websocket.send("sunk")
            await p[turn^3].websocket.send("sunk")
        elif(r == SIGNAL_LOST):
            return turn
        else:
            raise Exception()
        turn = turn^3

async def play_games():
    while 1:
        await asyncio.sleep(5)
        if(len(players) < 2):
            print("Too few players")
            continue
        p = [None] + random.sample(players, 2)  # 1-indexerad
        print(f"{p[1].name} vs {p[2].name}")
        try:
            winner = await play_game(p)
            if(winner == 0):
                await p[1].websocket.send("lost")
                await p[2].websocket.send("lost")
            else:
                await p[winner].websocket.send("won")
                await p[winner^3].websocket.send("lost")
            print(p[winner].name, "won!")
        except Exception:
            print("Error:")
            traceback.print_exc()

async def connect(websocket):
    global players
    name = None
    try:
        name = await websocket.recv()
        if(len(name) < 1):
            await websocket.send("för kort namn")
            return
        if(len(name) > 14):
            await websocket.send("för långt namn")
            return
        for c in name:
            if(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!\"#%&/()=?^*@£${[]}\\±®œøæ|©µπåäöÅÄÖé,.-;:_<>"):
                await websocket.send("namnet innehåller otillåtna tecken")
                return
        if(any([p.name==name for p in players])):
            await websocket.send("namnet är upptaget")
            return
        print(name, "connected")
        user = Player(name, websocket)
        players.append(user)
        await websocket.send("ok")
        await websocket.wait_closed()
    except (exceptions.ConnectionClosedError, exceptions.ConnectionClosedOK):
        pass
    if(name is not None):
        print(name, "disconnected")
        players = [p for p in players if p.name != name]

async def main():
    asyncio.create_task(play_games())
    async with serve(connect, "0.0.0.0", 1234, ping_interval=None):
        await asyncio.Future()

asyncio.run(main())