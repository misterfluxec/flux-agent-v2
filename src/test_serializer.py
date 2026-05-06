from pipecat.serializers.base_serializer import FrameSerializer
import json
import base64
from pipecat.frames.frames import InputAudioRawFrame, OutputAudioRawFrame, Frame

class JSONBase64Serializer(FrameSerializer):
    def __init__(self):
        pass
    
    async def serialize(self, frame: Frame):
        if isinstance(frame, OutputAudioRawFrame):
            data = base64.b64encode(frame.audio).decode("utf-8")
            return json.dumps({"type": "audio", "data": data})
        return None

    async def deserialize(self, data: str | bytes):
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            msg = json.loads(data)
            if msg.get("type") == "audio" and msg.get("data"):
                audio_bytes = base64.b64decode(msg["data"])
                # We need to specify sample_rate and num_channels but we can pass default ones or Pipecat fills them?
                return InputAudioRawFrame(audio=audio_bytes, sample_rate=16000, num_channels=1)
        except Exception:
            pass
        return None
