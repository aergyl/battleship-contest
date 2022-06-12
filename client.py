from random import random, randint


NAME = f"Player_{randint(100, 999)}"

def start_game(opponent, pnum):
    print("Spelar mot", opponent)
    print("Jag är spelare", pnum)
    return [
        (1, 1, 1, 2),
        (1, 4, 1, 6),
        (3, 1, 5, 1),
        (3, 3, 3, 6),
        (5, 3, 5, 7),
    ]

def shoot():
    row = randint(0, 9)
    col = randint(0, 9)
    print(f"Jag skjuter på {row} {col}.")
    return row, col

def result(r):
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
            await websocket.send(" ".join([" ".join(map(str, ship)) for ship in ships]))
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
