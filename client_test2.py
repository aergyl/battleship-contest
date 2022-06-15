from random import random, randint, shuffle, choice

#This AI searches with a randomized checkerboard pattern + intelligent hunting when hitting.

NAME = f"Player_{randint(100, 999)}"

def start_game(opponent, pnum):
    print("Spelar mot", opponent)
    print("Jag är spelare", pnum)

    global shots, shipsizes, checkerboard
    shots = []
    shots.append([False] * 12)
    for i in range(10):
        shots.append([False] + [None] * 10 + [False])
    shots.append([False] * 12)

    shipsizes = [2, 3, 3, 4, 5]
    checkerboard = []
    for i in range(1, 11):
        for j in range(1, 11, 2):
            checkerboard.append((i, j + i % 2))
    shuffle(checkerboard)

    hv = ['H', 'V']
    occupied = []
    occupied.append([True] * 12)
    for i in range(10):
        occupied.append([True] + [False] * 10 + [True])
    occupied.append([True] * 12)

    ships = []
    for size in reversed(shipsizes):
        done = False
        while not done:
            done = True
            ship = (randint(0, 9), randint(0, 9), choice(hv))
            for i in range(size):
                x = ship[1] + 1 + (ship[2] == 'H') * i
                y = ship[0] + 1 + (ship[2] == 'V') * i
                if occupied[x][y]:
                    done = False
                    break
        for i in range(-1, size + 1):
            x = ship[1] + 1 + (ship[2] == 'H') * i
            y = ship[0] + 1 + (ship[2] == 'V') * i
            x2 = x + (ship[2] == 'V')
            x3 = x - (ship[2] == 'V')
            y2 = y + (ship[2] == 'H')
            y3 = y - (ship[2] == 'H')
            occupied[x][y] = True
            occupied[x2][y2] = True
            occupied[x3][y3] = True
        ships.append(ship)
    return reversed(ships)

def score(x, y, x_dir=True, y_dir=True):
    s = 0
    if x_dir:
        k = x
        i = 0
        while shots[k][y] == None:
            k += 1
            s += 2 ** -i
            i += 1
        k = x
        i = 0
        while shots[k][y] == None:
            k -= 1
            s += 2 ** -i
            i += 1
    if y_dir:
        k = y
        i = 0
        while shots[x][k] == None:
            k += 1
            s += 2 ** -i
            i += 1
        k = y
        i = 0
        while shots[x][k] == None:
            k -= 1
            s += 2 ** -i
            i += 1
    return s

def remove_ship(size, x1, y1, x2, y2):
    shipsizes.remove(size)
    for x3 in range(x1, x2 + 1):
        for y3 in range(y1, y2 + 1):
            for i in range(-1, 2):
                for j in range(-1, 2):
                    shots[x3 + i][y3 + j] = False

def hunt_ship(x, y):
    #First identify top left square.
    x1, y1 = x, y
    x2, y2 = x, y
    while shots[x1][y1]:
        x1 -= 1
    x1 += 1
    while shots[x1][y1]:
        y1 -= 1
    y1 += 1
    #Then the down right square.
    while shots[x2][y2]:
        x2 += 1
    x2 -= 1
    while shots[x2][y2]:
        y2 += 1
    y2 -= 1
    size = (x2 - x1 + 1) * (y2 - y1 + 1)
    if size == shipsizes[-1]:
        remove_ship(size, x1, y1, x2, y2)
        return

    hunt_x = []
    hunt_y = []
    if size == 1:
        if shots[x - 1][y] == None:
            hunt_x.append((x - 1, y))
        if shots[x + 1][y] == None:
            hunt_x.append((x + 1, y))
        if shots[x][y - 1] == None:
            hunt_y.append((x, y - 1))
        if shots[x][y + 1] == None:
            hunt_y.append((x, y + 1))
    else:
        if shots[x - 1][y] or shots[x + 1][y]:
            if shots[x1 - 1][y] == None:
                hunt_x.append((x1 - 1, y))
            if shots[x2 + 1][y] == None:
                hunt_x.append((x2 + 1, y))
        if shots[x][y - 1] or shots[x][y + 1]:
            if shots[x][y1 - 1] == None:
                hunt_y.append((x, y1 - 1))
            if shots[x][y2 + 1] == None:
                hunt_y.append((x, y2 + 1))
    if not hunt_x and not hunt_y:
        remove_ship(size, x1, y1, x2, y2)
        return

    choices = []
    best = [0, 0]
    for c in hunt_x:
        s1 = score(*c, True, False)
        s2 = score(*c, False, True)
        if s1 > best[0] or (s1 == best[0] and s2 > best[1]):
            best[0] = s1
            best[1] = s2
            choices = [c]
        elif s1 == best[0] and s2 == best[1]:
            choices.append(c)
    for c in hunt_y:
        s1 = score(*c, False, True)
        s2 = score(*c, True, False)
        if s1 > best[0] or (s1 == best[0] and s2 > best[1]):
            best[0] = s1
            best[1] = s2
            choices = [c]
        elif s1 == best[0] and s2 == best[1]:
            choices.append(c)
    return choice(choices)

def get_shot():
    for x in range(1, 11):
        for y in range(1, 11):
            if shots[x][y]:
                hunt = hunt_ship(x, y)
                if hunt:
                    return hunt
    while True:
        x, y = checkerboard.pop()
        if shots[x][y] == None:
            return (x, y)

def shoot():
    global last_shot
    last_shot = get_shot()
    row = last_shot[1] - 1
    col = last_shot[0] - 1
    print(f"Jag skjuter på {row} {col}.")
    return row, col

def result(r):
    shots[last_shot[0]][last_shot[1]] = r != 'miss'
    if r == "miss":
        print("Jag missade.")
    elif r == "hit":
        print("Jag träffade!")
    elif r == "sunk":  # bara om det är påslaget
        print("Jag träffade och sänkte!")
    else: assert 0

def opp_shot(row, col):
    print(f"Motståndaren sköt på {row} {col}.")

def game_over(r):
    if r == "won":
        print("Jag vann spelet!")
    elif r == "lost":
        print("Jag förlorade :(")
    else:
        assert 0




#########################################################################
import time
import asyncio
from websockets import connect
import traceback

async def main():
    async with connect("ws://localhost:1234") as websocket:  # byt ut mot serverns ip
        await websocket.send(NAME)
        r = await websocket.recv()
        if r != "ok":
            print(r)
            return
        while True:
            msg = (await websocket.recv()).split()
            assert msg[0] == "play"
            opponent = msg[1]
            pnum = int(await websocket.recv())
            ships = start_game(opponent, pnum)
            await websocket.send(" ".join([f"{r} {c} {d}" for r,c,d in ships]))
            res = await websocket.recv()
            if res not in ["ok", "won", "lost"]:
                print(res)
                return
            if res != "lost":
                print("Placering godkänd")
            turn = 1
            while res != "won" and res != "lost":
                if turn == pnum:
                    r, c = shoot()
                    await websocket.send(f"{r} {c}")
                    res = await websocket.recv()
                    if res == "won" or res == "lost":
                        break
                    result(res)
                else:
                    res = await websocket.recv()
                    if res == "won":
                        break
                    r, c = map(int, res.split())
                    res = await websocket.recv()
                    opp_shot(r, c)
                turn ^= 3
            game_over(res)

while 1:
    try:
        asyncio.run(main())
    except Exception as e:
        traceback.print_exc()
    print("\n\nConnection lost. Retrying 10s...")
    time.sleep(10)
