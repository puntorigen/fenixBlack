import base64
import requests

class VoiceSynthesizer:
    def __init__(self, api_key, voice_id):
        self.api_key = api_key
        self.voice_id = voice_id
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"
        self.headers = {
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        self.model_id = "eleven_multilingual_v2"
        self.voice_settings = {
            "stability": 0.9,
            "similarity_boost": 0.55,
            "style": 0.1,
            "use_speaker_boost": True
        }
        self.audio_cache = {}  # Cache to store preloaded fillers
        self.preload_fillers()

    def preload_fillers(self):
        fillers = ["uhmm", "ahh"]
        for filler in fillers:
            self.audio_cache[filler] = self.get_audio_base64(filler)

    def text_to_speech(self, text: str, previous_text: str = "") -> tuple[bytes, float]:
        url = f"{self.base_url}/{self.voice_id}/with-timestamps?optimize_streaming_latency=0&output_format=ulaw_8000"
        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": self.voice_settings,
            "previous_text": previous_text
        }
        response = requests.post(url, json=data, headers=self.headers)
        if response.status_code == 200:
            response_json = response.json()
            audio_base64 = response_json['audio_base64']
            audio_bytes = base64.b64decode(audio_base64)
            timestamps = response_json['alignment']
            duration = timestamps['character_end_times_seconds'][-1] * 1000  # Convert last timestamp to milliseconds
            return audio_bytes, duration
        else:
            print(f"Error in text-to-speech conversion: {response.status_code}, {response.text}")
            return None, 0

    def get_audio_base64(self, text: str, previous_text: str = "") -> tuple[str, float]:
        if text in self.audio_cache:
            return self.audio_cache[text]
        audio_bytes, duration = self.text_to_speech(text, previous_text)
        if audio_bytes is not None:
            encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')
            self.audio_cache[text] = (encoded_audio, duration)
            return encoded_audio, duration
        return None, 0

    def generate_twilio_media_payload(self, text: str) -> dict:
        base64_audio, _ = self.get_audio_base64(text)
        if base64_audio:
            return {
                "event": "media",
                "media": {
                    "payload": base64_audio
                }
            }
        return {}
