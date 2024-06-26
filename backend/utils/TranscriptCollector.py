# utilities for call 'tool'
class TranscriptCollector:
    def __init__(self):
        self.reset()
        self.history = []

    def reset(self):
        self.transcript_parts = []

    def add_part(self, part):
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        joined = ' '.join(self.transcript_parts)
        self.history.append(joined)
        return joined
    
    def get_previous_sentence(self):
        if len(self.history) > 0:
            return self.history[-1]
        return ""
    
    def is_empty(self):
        # Check if there are no parts collected
        return len(self.transcript_parts) == 0

