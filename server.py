import websockets
import asyncio
import json
import time
import threading
import ssl
import pathlib
from game import Game
from games import Games

CURRENT_ID_COUNT = 0
GAMEVARS_PATH = "./gamevars.json"
with open(GAMEVARS_PATH, "r") as f:
    GAMEVARS = json.load(f)

class Client:
    def __init__(self, ws, name):
        self.ws = ws
        self.id = self.get_id()
        self.name = name
        self.game = None

    def get_id(self):
        global CURRENT_ID_COUNT
        CURRENT_ID_COUNT += 1
        return CURRENT_ID_COUNT - 1
    
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
GAMES = Games(msg_pool=PACKETS)

async def broadcast():
    global PACKETS
    while True:
        time.sleep(0.001)
        for p in PACKETS.packets:
            await p.ws.send(json.dumps(p.msg))
            time.sleep(0.001)
        PACKETS.clear()
        await asyncio.sleep(0)

asyncio.get_event_loop().create_task(broadcast())

async def handler(websocket, path):
    global CURRENT_ID_COUNT
    CLIENTS.add(websocket)
    print("Someone connected.")
    new_client = Client(websocket, name=f"GUEST{CURRENT_ID_COUNT}")
    await websocket.send(
        json.dumps(
        {
            "msg_type": "information",
            "information_type": "your_info",
            "content": {
                    "id": new_client.id,
                    "name": new_client.name
                }
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
    game = GAMES.join_any_game(new_client)
    if game.full():
        t = threading.Thread(target=game.start())
        t.start()
    try:
        async for msg in websocket:
            print(f"[received] {msg}")
            if game:
                msg = json.loads(msg)
                game.handle_player_msg(new_client, msg)
                # game.current_round.handle_player_actions(new_client, msg)
    finally:
        CLIENTS.remove(websocket)
        print("Someone disconnected.")


ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(
    pathlib.Path(__file__).with_name("localhost.pem"))

# start_server = websockets.serve(handler, "localhost", port=443)
start_server = websockets.serve(handler, "localhost", port=8765, ssl=ssl_context)
print("Here.")


asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()