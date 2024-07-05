#from tools.phone.utils import TranscriptCollector, VoiceSynthesizer, LanguageModelProcessor
import time, asyncio, random, json, io
import utils.ws_client as ws_client
import tools.phone.utils as phone_utils
from fastapi import WebSocketDisconnect

class CallManager:
    def __init__(self, audio_manager, session_obj, meeting_id, callsid, stream_sids, ws_audio, groq_api_key, eleven_labs_api_key, base_filler_threshold_ms=900, response_threshold_ms=2000, cooldown_period_ms=2000, extended_silence_ms=5000):
        self.audio_manager = audio_manager
        self.callsid = callsid
        self.stream_sids = stream_sids
        self.meeting_id = meeting_id
        self.session = session_obj
        self.ws_audio = ws_audio
        # TODO: use the ExpertSolo class as the language_processor
        #self.language_processor = phone_utils.LanguageModelProcessor(self.session["expert_ref"].expert.name,groq_api_key)
        self.language_processor = self.session["expert_ref"]
        # TODO: use the voice_id from ExpertSolo (when available)
        #self.synthethizer = phone_utils.VoiceSynthesizer(eleven_labs_api_key, voice_id="aEO01A4wXwd1O8GPgGlF")
        self.synthethizer = self.session["expert_ref"].synthethizer
        # TODO: add time tracking for the call to enforce required max_duration and request Expert to trigger end of conversation 
        self.not_complete_times = 0
        self.spoken = []
        self.notify_manager = ws_client.WebSocketClient(meeting_id) # where to notify events to the frontend & tools
        self.base_filler_threshold_ms = base_filler_threshold_ms
        self.cooldown_period_ms = cooldown_period_ms
        self.response_threshold_ms = response_threshold_ms
        self.extended_silence_ms = extended_silence_ms  # Time to wait before re-engaging after last user input
        self.last_audio_time = time.time() * 1000
        self.last_response_time = 0  # Track the last time a response was generated
        self.last_user_speak_time = 0  # Track the last time user spoke
        self.start_time = time.time() * 1000  # Record the start time of the conversation
        self.transcript_collector = phone_utils.TranscriptCollector()
        self.filler_triggered = False
        self.welcomed = False
        self.reset_timer()  # Initialize timer settings

    async def check_silence(self):
        if self.welcomed == False:
            await self.session["notify_ref"].from_tool("phone_call", "Phone call started")
            # self.session["intro"] should have the intro msg
            # self.session["language"] should have the required conversation language
            if self.session["intro"]:
                # speak intro message - TODO do this within the ExpertSolo class for adapting the intro to the target language
                # and for using the voice_id from the ExpertSolo (do this here on init)
                #message = self.session["intro"]
                # translate the message to the required language
                # if language is not en, nor starts with en-
                #if self.session["language"] != "en" and not self.session["language"].startswith("en-"):
                #    message = await self.session["expert_ref"].translate_from_english(message)
                #    print(f"Translated intro message to {self.session['language']}: {message}")
                message = self.session["expert_ref"].translated_intro
                await self.session["notify_ref"].from_tool("phone_call", f"[phone]: {message}")
                audio_duration_ms = await self.send_audio(message, "")
                self.spoken.append(message)  
                self.last_response_time = time.time() * 1000  # Update the last response time
                # make the expert say the FIRST question (translated); after the intro.
                first_question = self.session["expert_ref"].current_question 
                await self.session["notify_ref"].from_tool("phone_call", f"[phone]: {first_question}")
                audio_duration_ms = await self.send_audio(first_question, message)
                self.spoken.append(first_question) 
                self.last_response_time = time.time() * 1000  # Update the last response time

            self.welcomed = True
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
                    await self.trigger_filler()
                    self.filler_triggered = True

    async def generate_audio(self, text, previous_text=""):
        # pre-generates the audio and caches it for later use
        audio64, audio_duration_ms = self.synthethizer.get_audio_base64(text, previous_text)
        return audio_duration_ms
    
    async def send_audio(self, text, previous_text=""):
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
            await self.audio_manager.send_message(json.dumps(payload), self.meeting_id)
            return audio_duration_ms
        return 0
        
    async def trigger_response(self):
        full_sentence = self.transcript_collector.get_full_transcript().strip()
        prev_part = self.transcript_collector.get_previous_sentence()
        last_spoken = self.spoken[-1] if self.spoken else ""
        current_time = time.time() * 1000
        if full_sentence:
            is_complete = True
            # 4jul24, commented for now to avoid extra latency
            #if full_sentence != prev_part:
            #    test_start_time = time.time() * 1000
            #    is_complete = await self.language_processor.is_complete_sentence(prev_part, full_sentence)
            #    test_took = time.time() * 1000 - test_start_time
            #    print(f"Test took {test_took} ms")
            #    if self.not_complete_times > 1:
            #        print(f"not_complete_times>1, marking as complete for not repeating fillers too much")
            #        is_complete = True

            if is_complete == False:
                # TODO: check with groq and instructor if this 'full_sentence' looks indeed like a full sentence or just a part of it
                # if it's not a full sentence, we should wait for the next part to complete it and just say 'uhmm' or 'I see' or a filler word
                print(f"Response is not complete, waiting for next part",{ "current":full_sentence,"previous":prev_part })
                # only send audio if self.not_complete_times is odd
                if self.not_complete_times % 2 == 1:
                    audio_duration_ms = await self.send_audio("uhmm")
                self.not_complete_times += 1
                #self.reset_timer() 
            else:
                self.not_complete_times = 0
                print(f"[{current_time}] Processing response: {full_sentence}") # for {self.callsid}
                await self.session["notify_ref"].from_tool("phone_call", f"[{self.session["user_name"]} said]: {full_sentence}")
                response = await self.language_processor.query(full_sentence)
                # say/notify the expert response
                print(f"[{current_time}] Generated Response: {response}")
                await self.session["notify_ref"].from_tool("phone_call", f"[phone]: {response}") #->{self.session["expert_ref"].expert.name}
                # send the response to the audio_manager
                self.last_response_time = time.time() * 1000  # Update the last response time
                audio_duration_ms = await self.send_audio(response, last_spoken)
                self.spoken.append(response) 
                # Sleep to simulate the playback duration of the response audio
                audio_duration_seconds = audio_duration_ms / 1000
                print(f"[{current_time}] Generated Audio duration: {audio_duration_seconds} seconds")
                #asyncio.create_task(self.handle_response_delay(audio_duration_seconds))
                self.transcript_collector.reset()  # Reset the transcript collector after processing

                if self.session["expert_ref"].current_question is None:
                    # we have no more questions, we should end the call
                    # get the chat_history from the expert
                    chat_history = self.session["expert_ref"].get_chat_history()
                    # tell the tool to hangup
                    await self.session["notify_ref"].to_tool("phone_call_ended",{ "cmd":"transcription", "data":chat_history })
                    # sleep the goodbye audio duration before hanging up
                    await asyncio.sleep(audio_duration_seconds)
                    #raise WebSocketDisconnect
                    await self.ws_audio.close(code=1000) # disconnect twilio socket (to hangup)

            self.reset_timer() 

    async def handle_response_delay(self, delay_seconds):
        await asyncio.sleep(delay_seconds)
        # Reset the timer after the delay to ensure new audio handling is synced with the end of playback
        self.reset_timer()

    async def trigger_filler(self):
        if not self.transcript_collector.is_history_empty():  # Ensure there's been speech before filler
            current_time = time.time() * 1000
            #print(f"[{current_time}]-muted Inserting filler sound: ahh for {self.callsid}")
            # Here you can trigger the actual audio playback or send a command
            # asyncio.create_task(self.audio_manager.send_filler_sound(self.callsid, "uhmm"))
            #audio_duration_ms = await self.send_audio("ahh")
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
