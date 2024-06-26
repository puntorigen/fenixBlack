import time, asyncio, random, json, io
from . import TranscriptCollector, VoiceSynthesizer, LanguageModelProcessor, WebSocketClient

class CallManager:
    def __init__(self, audio_manager, meeting_id, callsid, stream_sids, groq_api_key, eleven_labs_api_key, base_filler_threshold_ms=900, response_threshold_ms=2000, cooldown_period_ms=2000, extended_silence_ms=5000):
        self.audio_manager = audio_manager
        self.callsid = callsid
        self.stream_sids = stream_sids
        self.meeting_id = meeting_id
        self.language_processor = LanguageModelProcessor("Gabriela",groq_api_key)
        self.synthethizer = VoiceSynthesizer(eleven_labs_api_key, voice_id="aEO01A4wXwd1O8GPgGlF")
        #self.notify_manager = WebSocketClient(meeting_id) # where to notify events to the frontend & tools
        self.base_filler_threshold_ms = base_filler_threshold_ms
        self.cooldown_period_ms = cooldown_period_ms
        self.response_threshold_ms = response_threshold_ms
        self.extended_silence_ms = extended_silence_ms  # Time to wait before re-engaging after last user input
        self.last_audio_time = time.time() * 1000
        self.last_response_time = 0  # Track the last time a response was generated
        self.last_user_speak_time = 0  # Track the last time user spoke
        self.start_time = time.time() * 1000  # Record the start time of the conversation
        self.transcript_collector = TranscriptCollector()
        self.filler_triggered = False
        self.reset_timer()  # Initialize timer settings

    async def check_silence(self):
        while True:
            await asyncio.sleep(min(self.filler_threshold_ms, self.response_threshold_ms) / 1000)
            current_time = time.time() * 1000
            elapsed_time = current_time - self.last_audio_time
            elapsed_since_response = current_time - self.last_response_time
            elapsed_since_start = current_time - self.start_time
            elapsed_since_user_speak = current_time - self.last_user_speak_time

            if not self.transcript_collector.is_empty():
                if elapsed_time >= self.response_threshold_ms:
                    await self.trigger_response()
                    #self.reset_timer()
                    continue

            # Skip the filler logic if within the initial cooldown period after the start
            if elapsed_since_start <= self.cooldown_period_ms:
                continue

             # Handle filler sound logic
            if elapsed_since_response > self.cooldown_period_ms and elapsed_time >= self.filler_threshold_ms:
                if not self.filler_triggered:
                    self.trigger_filler()
                    self.filler_triggered = True

    def send_audio(self, text, previous_text=""):
        audio64, audio_duration_ms = self.synthethizer.get_audio_base64(text, previous_text)
        stream_sid = self.stream_sids.get(self.callsid, None)
        if stream_sid:
            payload = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": audio64
                }
            }
            asyncio.create_task(self.audio_manager.send_message(json.dumps(payload), self.meeting_id))
            return audio_duration_ms
        return 0
        
    async def trigger_response(self):
        full_sentence = self.transcript_collector.get_full_transcript().strip()
        prev_part = self.transcript_collector.get_previous_sentence()
        current_time = time.time() * 1000
        if full_sentence:
            is_complete = True
            if full_sentence != prev_part:
                test_start_time = time.time() * 1000
                test = await self.language_processor.is_complete_sentence(prev_part, full_sentence)
                test_took = time.time() * 1000 - test_start_time
                print(f"Test took {test_took} ms")
                is_complete = test.does_it_look_complete

            if is_complete == False:
                # TODO: check with groq and instructor if this 'full_sentence' looks indeed like a full sentence or just a part of it
                # if it's not a full sentence, we should wait for the next part to complete it and just say 'uhmm' or 'I see' or a filler word
                print(f"Response is not complete, waiting for next part",{ "current":full_sentence,"previous":prev_part })
                audio_duration_ms = self.send_audio("uhmm")
                self.reset_timer()
            else:
                print(f"[{current_time}] Processing response: {full_sentence}") # for {self.callsid}
                response = self.language_processor.process(full_sentence)
                #response = self.process_response(full_transcript)
                print(f"[{current_time}] Generated Response: {response}")
                
                # send the response to the audio_manager
                audio_duration_ms = self.send_audio(response, prev_part)

                # Sleep to simulate the playback duration of the response audio
                audio_duration_seconds = audio_duration_ms / 1000
                print(f"[{current_time}] Generated Audio duration (sleeping): {audio_duration_seconds} seconds")
                asyncio.create_task(self.handle_response_delay(audio_duration_seconds))
                self.last_response_time = time.time() * 1000  # Update the last response time
                self.transcript_collector.reset()  # Reset the transcript collector after processing

    async def handle_response_delay(self, delay_seconds):
        await asyncio.sleep(delay_seconds)
        # Reset the timer after the delay to ensure new audio handling is synced with the end of playback
        self.reset_timer()

    def trigger_filler(self):
        if not self.transcript_collector.is_empty():  # Ensure there's been speech before filler
            current_time = time.time() * 1000
            print(f"[{current_time}] Inserting filler sound: uhmm for {self.callsid}")
            # Here you can trigger the actual audio playback or send a command
            # asyncio.create_task(self.audio_manager.send_filler_sound(self.callsid, "uhmm"))
            self.filler_triggered = True
            self.reset_timer()  # Reset the timer to recalibrate silence detection

    def process_response(self, text):
        # Placeholder for processing text through LLM and generating audio
        current_time = time.time() * 1000
        return f"[{current_time}] Response to: {text}"

    def reset_timer(self):
        self.last_audio_time = time.time() * 1000
        self.filler_triggered = False
        self.filler_threshold_ms = self.base_filler_threshold_ms + random.randint(-300, 300)
        if hasattr(self, '_silence_task') and self._silence_task and not self._silence_task.cancelled():
            self._silence_task.cancel()
        self._silence_task = asyncio.create_task(self.check_silence())

    def add_transcription_part(self, text):
        if text.strip():  # Only add non-empty parts
            self.transcript_collector.add_part(text)
            self.last_user_speak_time = time.time() * 1000  # Update last user speak

    def cleanup(self):
        # If the SilenceManager is being cleaned up, ensure to cancel the task
        if hasattr(self, '_silence_task') and self._silence_task and not self._silence_task.cancelled():
            self._silence_task.cancel()
        print(f"Cleanup resources for {self.callsid}")
