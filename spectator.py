import sys
import asyncio
from websockets import connect
import pyglet as pg
from itertools import product

window = pg.window.Window(255, 605, 'Battleships!')

batch = pg.graphics.Batch()
squares = {}
colors = {
    "miss": (50, 50, 50),
    "hit": (150, 150, 50),
    "sunk": (250, 150, 150),
    "lost": (200, 0, 0)
}
for x, y, p in product(range(10), range(10), range(1, 3)):
    squares[x, y, p] = pg.shapes.Rectangle(25 * x + 5, 930 - 25 * y - 350 * p, 20, 20, color=(55, 55, 255), batch=batch)
label1 = pg.text.Label('(Player 1)', x=5, y=260, anchor_x='left', batch=batch)
label2 = pg.text.Label('(Player 2)', x=250, y=335, anchor_x='right', batch=batch)
label3 = pg.text.Label('---', x=127, y=290, anchor_x='center', font_size=24, batch=batch)

def reset_squares():
    for x, y, p in product(range(10), range(10), range(1, 3)):
        squares[x, y, p].color = (55, 55, 255)

def reset_labels(p1, p2):
    label1.text = p1
    label2.text = p2
    label3.text = '---'


async def window_loop():
    while not window.has_exit:
        await asyncio.sleep(0.05)
        window.dispatch_events()
        window.clear()
        batch.draw()
        window.flip()
    sys.exit()

async def main():
    asyncio.create_task(window_loop())
    async with connect("ws://localhost:1234") as websocket:  # byt ut mot serverns ip
        await websocket.send("*** SPECTATOR ***")
        async for msg in websocket:
            cmd, *args = msg.split()
            if(cmd == "new_game"):
                reset_squares()
                reset_labels(*args)
            elif(cmd == "moves"):
                label3.text = str(int(args[0]) // 2 + 1)
            elif(cmd == "color"):
                col, row, turn = map(int, args[:3])
                squares[col, row, turn].color = colors[args[3]]
            elif(cmd == "winner"):
                print("Player", args[0], "won!")

asyncio.run(main())
