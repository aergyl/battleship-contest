import asyncio
from websockets import serve, exceptions
import random
import time
from constants import *
from fleet import Fleet

class Player:
    def __init__(self, name, websocket):
        self.name = name
        self.websocket = websocket
        self.playing = False
    
    async def trysend(self, msg):
        try:
            await self.websocket.send(msg)
        except:
            pass

    # Let player build fleet
    async def new_game(self, opp, pnum):
        assert not self.playing
        try:
            self.playing = True
            self.pnum = pnum
            await self.websocket.send("play " + opp.name)
            self.websocket.messages.clear()  # in case there are old messages from a timeout
            await self.websocket.send(str(pnum))
            fleet = Fleet()
            r = await asyncio.wait_for(self.websocket.recv(), timeout=TIMELIMIT_PLACE)
            shipsizes = []
            for size in FLEET_DIM:
                shipsizes += [size] * FLEET_DIM[size]
            shipsizes.sort()
            try:
                r = r.split()
                for i in range(0, len(r), 3):
                    row, col, dir = r[i : i+3]
                    row, col, idx = int(row), int(col), int(dir == 'H')
                    row2 = row + shipsizes[i//3][idx]-1
                    col2 = col + shipsizes[i//3][1 - idx]-1
                    fleet.add_ship(col, row, col2, row2)  # assuming pos x = down
                if(not fleet.validate() or len(r) != 3 * sum(FLEET_DIM.values())):
                    raise Exception()
            except:
                await self.trysend("invalid fleet")
                return None
            fleet.setup()
            return fleet
        except:
            return None
    
    async def game_over(self, winner):
        assert self.playing
        self.playing = False
        if(winner == self.pnum):
            await self.trysend("won")
        else:
            await self.trysend("lost")

players = []
spectators = []
spectator_msgs = []  # for new spectators to catch up with this game

async def send_to_spectators(msg):
    spectator_msgs.append(msg)
    i = 0
    # saving len in case someone connects while in the loop
    len_spec = len(spectators)
    while i < len_spec:
        try:
            await spectators[i].send(msg)
        except:
            spectators.pop(i)
            len_spec -= 1
        else:
            i += 1

async def play_game(p):
    spectator_msgs.clear()
    await send_to_spectators(f"new_game {p[1].name} {p[2].name}")
    task1 = asyncio.create_task(p[1].new_game(p[2], 1))
    task2 = asyncio.create_task(p[2].new_game(p[1], 2))
    fleets = [None, await task1, await task2]  # 1-indexed
    if(fleets[1] is None): return 2
    if(fleets[2] is None): return 1
    await p[1].trysend("ok")
    await p[2].trysend("ok")
    moves = 0
    turn = 1
    prevmove_time = time.time()
    while 1:
        await asyncio.sleep(SHOOT_MINTIME - (time.time()-prevmove_time))
        prevmove_time = time.time()
        await send_to_spectators(f"moves {moves}")
        try:
            r = await asyncio.wait_for(p[turn].websocket.recv(), timeout=TIMELIMIT_SHOOT)
            row, col = map(int, r.split())
            r = fleets[turn^3].get_hit_by(col, row)  # assuming pos x = down
        except:
            return turn^3
        r = fleets[turn^3].get_hit_by(col, row)  # assuming pos x = down
        
        try:
            await p[turn^3].websocket.send(f"{row} {col}")
        except:
            return turn
        if(r == SIGNAL_MISS):
            s = "miss"
        elif(r == SIGNAL_HIT):
            s = "hit"
        elif(r == SIGNAL_SUNK):
            s = "sunk"
        elif(r == SIGNAL_LOST):
            return turn
        else:
            raise Exception()
        moves += 1
        if(moves == MAX_NUM_OF_SHOTS):
            return random.randint(1, 2)  # Random winner
        await p[turn].trysend(s)
        await p[turn^3].trysend(s)
        await send_to_spectators(f"color {col} {row} {turn} {s}")
        turn = turn^3

async def play_games():
    while 1:
        await asyncio.sleep(REST_TIME)
        if(len(players) < 2):
            print("Too few players")
            continue
        p = [None] + random.sample(players, 2)  # 1-indexed
        print(f"{p[1].name} vs {p[2].name}")
        winner = await play_game(p)
        assert winner in [1,2]
        await p[1].game_over(winner)
        await p[2].game_over(winner)
        await send_to_spectators(f"winner {winner}")
        print(p[winner].name, "won!")

async def connect(websocket):
    global players
    name = None
    try:
        name = await websocket.recv()
        if(name == "*** SPECTATOR ***"):
            i = 0
            while i < len(spectator_msgs):
                try: await websocket.send(spectator_msgs[i])
                except: return
                i+=1
            spectators.append(websocket)
            await websocket.wait_closed()
            return
        if(len(name) < 1):
            await websocket.send("för kort namn")
            return
        if(len(name) > 14):
            await websocket.send("för långt namn")
            return
        for c in name:
            if(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+!\"#%&/()=?^*@£${[]}\\±®œøæ|©µπåäöÅÄÖé,.-;:_<>"):
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
