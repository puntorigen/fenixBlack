# utilities for call 'tool'
class TranscriptCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.transcript_parts = []

    def add_part(self, part):
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        return ' '.join(self.transcript_parts)
    
    def is_empty(self):
        # Check if there are no parts collected
        return len(self.transcript_parts) == 0

