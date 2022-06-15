from random import random, randint, shuffle, choice


NAME = f"Player_{randint(100, 999)}"

def start_game(opponent, pnum):
    print("Spelar mot", opponent)
    print("Jag är spelare", pnum)

    global shots
    shots = []
    shots.append([False] * 12)
    for i in range(10):
        shots.append([False] + [None] * 10 + [False])
    shots.append([False] * 12)

    hv = ['H', 'V']
    shipsizes = [5, 4, 3, 3, 2]
    occupied = []
    occupied.append([True] * 12)
    for i in range(10):
        occupied.append([True] + [False] * 10 + [True])
    occupied.append([True] * 12)

    ships = []
    for size in shipsizes:
        done = False
        while not done:
            done = True
            ship = (randint(0, 9), randint(0, 9), choice(hv))
            for i in range(size):
                x = ship[0] + 1 + (ship[2] == 'H') * i
                y = ship[1] + 1 + (ship[2] == 'V') * i
                if occupied[x][y]:
                    done = False
                    break
        for i in range(-1, size + 1):
            x = ship[0] + 1 + (ship[2] == 'H') * i
            y = ship[1] + 1 + (ship[2] == 'V') * i
            occupied[x][y] = True
            x2 = x + (ship[2] == 'V')
            x3 = x - (ship[2] == 'V')
            y2 = y + (ship[2] == 'H')
            y3 = y - (ship[2] == 'H')
            occupied[x2][y2] = True
            occupied[x3][y3] = True
        ships.append((ship[1], ship[0], ship[2]))
    return reversed(ships)

def get_shot():
    empty = []
    for x in range(1, 11):
        for y in range(1, 11):
            if shots[x][y] == 'hit':
                if shots[x - 1][y] == 'hit':
                    x2 = x - 1
                    while shots[x2][y] == 'hit':
                        shots[x2][y - 1] = False
                        shots[x2][y + 1] = False
                        x2 -= 1
                    if shots[x2][y] == None:
                        return (x2, y)
                if shots[x + 1][y] == 'hit':
                    x2 = x + 1
                    while shots[x2][y] == 'hit':
                        shots[x2][y - 1] = False
                        shots[x2][y + 1] = False
                        x2 += 1
                    if shots[x2][y] == None:
                        return (x2, y)
                elif shots[x][y - 1] == 'hit':
                    y2 = y - 1
                    while shots[x][y2] == 'hit':
                        shots[x + 1][y2] = False
                        shots[x - 1][y2] = False
                        y2 -= 1
                    if shots[x][y2] == None:
                        return (x, y2)
                elif shots[x][y + 1] == 'hit':
                    y2 = y + 1
                    while shots[x][y2] == 'hit':
                        shots[x + 1][y2] = False
                        shots[x - 1][y2] = False
                        y2 += 1
                    if shots[x][y2] == None:
                        return (x, y2)
                elif shots[x - 1][y] == None:
                    return (x - 1, y)
                elif shots[x + 1][y] == None:
                    return (x + 1, y)
                elif shots[x][y - 1] == None:
                    return (x, y - 1)
                elif shots[x][y + 1] == None:
                    return (x, y + 1)
            elif shots[x][y] == None:
                empty.append((x, y))
    best = [0, 0]
    shuffle(empty)
    for p in empty:
        s = 0
        k = p[1]
        i = 0
        while shots[p[0]][k] == None:
            k += 1
            s += 2 ** -i
            i += 1
        k = p[1]
        i = 0
        while shots[p[0]][k] == None:
            k -= 1
            s += 2 ** -i
            i += 1
        k = p[0]
        i = 0
        while shots[k][p[1]] == None:
            k += 1
            s += 2 ** -i
            i += 1
        k = p[0]
        i = 0
        while shots[k][p[1]] == None:
            k -= 1
            s += 2 ** -i
            i += 1
        if s > best[0]:
            best[0] = s
            best[1] = p
    return best[1]

def shoot():
    global last_shot
    last_shot = get_shot()
    row = last_shot[1] - 1
    col = last_shot[0] - 1
    print(f"Jag skjuter på {row} {col}.")
    return row, col

def result(r):
    shots[last_shot[0]][last_shot[1]] = r
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
