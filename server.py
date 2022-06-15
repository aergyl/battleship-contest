import asyncio
from websockets import serve, exceptions
import random
from constants import *
from fleet import Fleet
import pyglet as pg
from itertools import product

game_speed = 0.3
window = pg.window.Window(255, 605, 'Battleships!')

@window.event
def on_key_press(key, mod):
    global game_speed
    if key == pg.window.key.SPACE:
        game_speed = 0.03

@window.event
def on_key_release(key, mod):
    global game_speed
    if key == pg.window.key.SPACE:
        game_speed = 0.3

batch = pg.graphics.Batch()
squares = {}
colors = {
    SIGNAL_MISS: (50, 50, 50),
    SIGNAL_HIT: (150, 150, 50),
    SIGNAL_SUNK: (250, 150, 150),
    SIGNAL_LOST: (255, 255, 255)
}
for x, y, p in product(range(10), range(10), range(1, 3)):
    squares[x, y, p] = pg.shapes.Rectangle(25 * x + 5, 930 - 25 * y - 350 * p, 20, 20, color=(55, 55, 255), batch=batch)
label1 = pg.text.Label('(Player 1)', x=5, y=260, anchor_x='left', batch=batch)
label2 = pg.text.Label('(Player 2)', x=250, y=335, anchor_x='right', batch=batch)
label3 = pg.text.Label('---', x=127, y=290, anchor_x='center', font_size=24, batch=batch)

def reset_squares():
    for x, y, p in product(range(10), range(10), range(1, 3)):
        squares[x, y, p].color = (55, 55, 255)

def reset_labels(p):
    label1.text = p[1].name
    label2.text = p[2].name
    label3.text = '---'


async def window_loop():
    while not window.has_exit:
        await asyncio.sleep(0.05)
        window.dispatch_events()
        window.clear()
        batch.draw()
        window.flip()

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

async def play_game(p):
    reset_squares()
    reset_labels(p)
    task1 = asyncio.create_task(p[1].new_game(p[2], 1))
    task2 = asyncio.create_task(p[2].new_game(p[1], 2))
    fleets = [None, await task1, await task2]  # 1-indexerad
    if(fleets[1] is None): return 2
    if(fleets[2] is None): return 1
    await p[1].trysend("ok")
    await p[2].trysend("ok")
    moves = 0
    turn = 1
    while 1:
        try:
            #Hold down space to speed up.
            await asyncio.sleep(game_speed)
            label3.text = str(moves // 2 + 1)
            r = await asyncio.wait_for(p[turn].websocket.recv(), timeout=TIMELIMIT_SHOOT)
            row, col = map(int, r.split())
            r = fleets[turn^3].get_hit_by(col, row)  # assuming pos x = down
        except:
            return turn^3
        r = fleets[turn^3].get_hit_by(col, row)  # assuming pos x = down
        squares[col, row, turn].color = colors[r]
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
            return random.randint(1, 2)  # Slumpmässig vinnare
        await p[turn].trysend(s)
        await p[turn^3].trysend(s)
        turn = turn^3

async def play_games():
    while not window.has_exit:
        await asyncio.sleep(5)
        if(len(players) < 2):
            print("Too few players")
            continue
        p = [None] + random.sample(players, 2)  # 1-indexerad
        print(f"{p[1].name} vs {p[2].name}")
        winner = await play_game(p)
        assert winner in [1,2]
        await p[1].game_over(winner)
        await p[2].game_over(winner)
        print(p[winner].name, "won!")

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
        await window_loop()

asyncio.run(main())