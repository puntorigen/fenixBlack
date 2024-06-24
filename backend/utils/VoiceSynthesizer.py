import os
import base64
from io import BytesIO
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

class VoiceSynthesizer:
    def __init__(self, api_key, voice_id):
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.voice_settings = VoiceSettings(
            stability=0.59,
            similarity_boost=0.55,
            style=0.0,
            use_speaker_boost=True,
        )
        self.model_id = "eleven_multilingual_v2"
        self.output_format = "ulaw_8000"
        self.audio_cache = {}  # Cache to store preloaded fillers
        self.preload_fillers()

    def preload_fillers(self):
        # List of common fillers to preload
        fillers = ["uhmm", "ahh", "let me see"]
        for filler in fillers:
            self.audio_cache[filler] = self.get_audio_base64(filler)

    def text_to_speech_stream(self, text: str) -> BytesIO:
        """ Converts text to speech and returns a stream of audio data. """
        try:
            response = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                optimize_streaming_latency="0",
                output_format=self.output_format,
                text=text,
                model_id=self.model_id,
                voice_settings=self.voice_settings,
            )

            audio_stream = BytesIO()
            for chunk in response:
                if chunk:
                    audio_stream.write(chunk)
            audio_stream.seek(0)
            return audio_stream

        except Exception as e:
            print(f"Failed to synthesize text: {e}")
            return None

    def get_audio_base64(self, text: str) -> str:
        """ Converts text to speech and encodes it as base64 for transmission. """
        if text in self.audio_cache:
            return self.audio_cache[text]  # Return from cache if available

        audio_stream = self.text_to_speech_stream(text)
        if audio_stream:
            encoded_audio = base64.b64encode(audio_stream.getvalue()).decode('utf-8')
            self.audio_cache[text] = encoded_audio  # Cache this new audio
            return encoded_audio
        return None

    def generate_twilio_media_payload(self, text: str) -> dict:
        """ Generates a JSON payload for sending audio media to Twilio via WebSocket. """
        base64_audio = self.get_audio_base64(text)
        if base64_audio:
            return {
                "event": "media",
                "media": {
                    "payload": base64_audio
                }
            }
        return {}
