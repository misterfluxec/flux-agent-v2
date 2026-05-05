import asyncio
import base64
import urllib.request
import os

from services.multimedia import ServicioMultimedia

async def main():
    # 1. Download a short audio sample (e.g. from a public URL or use a tiny generated file)
    # Since we might not have internet or the URL might be dead, let's create a minimal valid WAV file in base64.
    # This is a 1-second 8kHz mono PCM WAV with silence. Faster-whisper might just output nothing, but it tests the pipeline.
    # Actually, let's download a real English sample audio to see if it transcribes it.
    
    # 1. Generar un archivo de audio WAV de silencio de 1 segundo en memoria
    import wave
    import io
    import struct

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        # Escribir 1 segundo de silencio
        for _ in range(16000):
            wav.writeframes(struct.pack('<h', 0))
    
    audio_bytes = buffer.getvalue()
    print("Audio generado, tamaño:", len(audio_bytes), "bytes")
    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
    
    print("Iniciando transcripción con faster-whisper...")
    texto = await ServicioMultimedia.transcribir_audio(b64_audio)
    print(f"Resultado de transcripción: '{texto}'")

if __name__ == "__main__":
    asyncio.run(main())
