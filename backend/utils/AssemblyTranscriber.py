import assemblyai as aai

TWILIO_SAMPLE_RATE = 8000 # Hz

class AssemblyTranscriber(aai.RealtimeTranscriber):
    def __init__(self, api_key, callback_partial=None, callback_final=None):
        super().__init__(
            on_data=self.on_data,
            on_error=self.on_error,
            on_open=self.on_open, # optional
            on_close=self.on_close, # optional
            sample_rate=TWILIO_SAMPLE_RATE,
            encoding=aai.AudioEncoding.pcm_mulaw
        )
        self.api_key = api_key
        self.callback_partial = callback_partial
        self.callback_final = callback_final

    def on_data(self, transcript: aai.RealtimeTranscript):
        """Handle incoming data (transcriptions)."""
        if not transcript.text:
            return None
        
        print("Transcribed Text: ", transcript.text)
        if isinstance(transcript, aai.RealtimeFinalTranscript):
            if self.callback_final:
                self.callback_final(transcript.text)
        else:
            if self.callback_partial:
                self.callback_partial(transcript.text)

    def on_open(self, session_opened: aai.RealtimeSessionOpened):
        "Called when the connection has been established."
        print("Session ID:", session_opened.session_id)

    def on_error(self, error: aai.RealtimeError):
        "Called when the connection has been closed."
        print("An error occured:", error)


    def on_close(self):
        "Called when the connection has been closed."
        print("Closing Session")