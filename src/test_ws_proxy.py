import asyncio
import websockets
import json
import base64
import struct
import math

def generate_sine_wave(freq=500, sample_rate=16000, duration_secs=1.5, amplitude=16000):
    """Generate PCM16 sine wave audio to trigger VAD"""
    num_samples = int(sample_rate * duration_secs)
    audio_bytes = bytearray(num_samples * 2)  # 2 bytes per sample (int16)
    for i in range(num_samples):
        sample = int(amplitude * math.sin(2 * math.pi * freq * i / sample_rate))
        # Pack as little-endian int16
        struct.pack_into('<h', audio_bytes, i * 2, sample)
    return bytes(audio_bytes)

async def test():
    try:
        async with websockets.connect("ws://127.0.0.1:8002/api/v1/sales/voice/stream") as websocket:
            print("Connected to FastAPI backend, waiting for pipeline to be ready...")
            await asyncio.sleep(2)
            
            # Generate a 1.5s 500Hz sine wave (speech-like volume) to trigger VAD
            sine_audio = generate_sine_wave(freq=440, duration_secs=1.5)
            print(f"Sending {len(sine_audio)} bytes of sine wave audio")
            
            # Send in chunks like a real browser would (20ms frames = 640 bytes each)
            chunk_size = 640
            for i in range(0, len(sine_audio), chunk_size):
                chunk = sine_audio[i:i+chunk_size]
                base64_chunk = base64.b64encode(chunk).decode("utf-8")
                await websocket.send(json.dumps({"type": "audio", "data": base64_chunk}))
                await asyncio.sleep(0.02)  # 20ms inter-frame delay
            
            print("All audio chunks sent, waiting for STT/LLM/TTS response...")
            
            # Wait up to 30s for a response (LLM can be slow)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                print(f"Got response: {str(response)[:200]}")
            except asyncio.TimeoutError:
                print("Timeout waiting for response (30s)")
            
            await websocket.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed: {e}")

asyncio.run(test())
