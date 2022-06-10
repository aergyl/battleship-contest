from random import random, randint


def place_ships():
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
    print("Det blev en", r)

def opp_shot(row, col):
    print(f"Motståndaren sköt på {row} {col}.")

def game_over(r):
    print(f"Spelet slut. Jag {r}.")




#########################################################################
import asyncio
from websockets import connect

async def main():
    async with connect("ws://localhost:1234") as websocket:  # byt ut mot serverns ip
        await websocket.send(f"Player_{randint(100, 999)}")
        r = await websocket.recv()
        if r != "ok":
            print(r)
            return
        while True:
            msg = await websocket.recv()
            assert(msg[0:5] == "play ")
            opponent = msg.split()[1]
            print("Spelar mot", opponent)
            pnum = int(await websocket.recv())
            print("Jag är spelare", pnum)
            ships = place_ships()
            for ship in ships:
                await websocket.send(" ".join(map(str, ship)))
            res = await websocket.recv()
            if res != "ok" and res != "won":
                print(res)
                return
            print("Placering godkänd")
            turn = 1
            while res != "won" and res != "lost":
                if(turn == pnum):
                    r, c = shoot()
                    await websocket.send(f"{r} {c}")
                    res = await websocket.recv()
                    if(res == "won"):
                        break
                    result(res)
                else:
                    res = await websocket.recv()
                    if(res == "won"):
                        break
                    r, c = map(int, res.split())
                    res = await websocket.recv()
                    opp_shot(r, c)
                turn ^= 3
            game_over(res)

asyncio.run(main())
