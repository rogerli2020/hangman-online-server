from grpc import GenericRpcHandler
import websockets
import asyncio
import json
import time
import threading

CLIENTS = set()

class Packet:
    def __init__(self, ws, msg) -> None:
        self.ws = ws
        self.msg = msg

PACKETS = []

def generate_packets():
    while True:
        time.sleep(10)
        for c in CLIENTS:
            PACKETS.append(Packet(c, f"Current Time: [{time.time()}]"))

t = threading.Thread(target=generate_packets)
t.start()

async def broadcast():
    def getAllPackets():
        ret = []
        while len(PACKETS) != 0:
            ret.append(PACKETS.pop())
        return ret
    while True:
        await asyncio.gather(
            *[Packet.ws.send(json.dumps({"msg_type": "chat", "content": Packet.msg})) for Packet in getAllPackets()],
            return_exceptions=False,
        )
        await asyncio.sleep(0.001)

asyncio.get_event_loop().create_task(broadcast())

async def handler(websocket, path):
    CLIENTS.add(websocket)
    try:
        async for msg in websocket:
            print(msg)
            PACKETS.append(Packet(websocket, "ECHO " + msg))
    finally:
        CLIENTS.remove(websocket)

# start_server = websockets.serve(handler, "localhost", 8765)
start_server = websockets.serve(handler, port=8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()