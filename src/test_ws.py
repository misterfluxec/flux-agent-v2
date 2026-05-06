import asyncio
import websockets

async def test():
    try:
        async with websockets.connect("ws://127.0.0.1:8002/api/v1/sales/voice/stream") as websocket:
            print("Connected directly to backend!")
            await websocket.close()
    except Exception as e:
        print(f"Failed: {e}")

asyncio.run(test())
