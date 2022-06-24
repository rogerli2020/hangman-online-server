import websockets
import asyncio
import json
import time
import threading
from game import Game

CURRENT_ID_COUNT = 0
GAMEVARS_PATH = "./gamevars.json"
with open(GAMEVARS_PATH, "r") as f:
    GAMEVARS = json.load(f)

class Client:
    def __init__(self, ws):
        self.ws = ws
        self.id = self.get_id()

    def get_id(self):
        global CURRENT_ID_COUNT
        CURRENT_ID_COUNT += 1
        return CURRENT_ID_COUNT
    
    async def send(self, msg):
        await self.ws.send(msg)

class Packet:
    def __init__(self, ws, msg) -> None:
        self.ws = ws
        self.msg = msg

class Packets:
    def __init__(self) -> None:
        self.packets = []
    
    def push(self, ws, msg):
        self.packets.append(Packet(ws, msg))
    
    def empty(self):
        return len(self.packets) == 0
    
    def load(self, list):
        list.extend(self.packets)
        self.packets = []
    
    def clear(self):
        self.packets = []

CLIENTS = set()
PACKETS = Packets()
GAME = Game(PACKETS, id=1)

async def broadcast():
    global PACKETS
    while True:
        for p in PACKETS.packets:
            await p.ws.send(json.dumps(p.msg))
            time.sleep(0.001)
        PACKETS.clear()
        await asyncio.sleep(0)

asyncio.get_event_loop().create_task(broadcast())

async def handler(websocket, path):
    CLIENTS.add(websocket)
    new_client = Client(websocket)
    await websocket.send(
        json.dumps(
        {
            "msg_type": "information",
            "information_type": "your_id",
            "content": new_client.id
            }
        )
    )
    await asyncio.sleep(0.1)
    await websocket.send(
        json.dumps(
            {
                "msg_type": "information",
                "information_type": "GAMEVARS",
                "content": GAMEVARS
            }
        )
    )
    await asyncio.sleep(0.1)
    GAME.add_player(new_client)
    if GAME.full():
        t = threading.Thread(target=GAME.start())
        t.start()
    try:
        async for msg in websocket:
            print(f"[received] {msg}")
            # PACKETS.append(Packet(websocket, "ECHO " + msg))
    finally:
        CLIENTS.remove(websocket)

start_server = websockets.serve(handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()