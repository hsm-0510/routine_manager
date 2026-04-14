from collections import defaultdict

class BufferManager:
    def __init__(self):
        self.buffer = defaultdict(list)
        self.processed_flags = {}  # prevents duplicate predictions

    def add_event(self, event):
        trailer = event["TRAILER_CODE"]
        self.buffer[trailer].append(event)
        return trailer

    def get_buffer(self, trailer):
        return self.buffer[trailer]

    def size(self, trailer):
        return len(self.buffer[trailer])

    def clear(self, trailer):
        self.buffer[trailer].clear()

    def mark_processed(self, trailer):
        self.processed_flags[trailer] = True

    def is_processed(self, trailer):
        return self.processed_flags.get(trailer, False)

    def reset(self, trailer):
        self.buffer[trailer].clear()
        self.processed_flags[trailer] = False