class EventPipe:
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)

    def push(self, event):
        data = event
        for handler in self.handlers:
            data = handler(data)
        return data

# This is ugly code duplicating, but we dont have Promises
class AsyncEventPipe(EventPipe):
    async def push(self, event):
        data = event
        for handler in self.handlers:
            data = await handler(data)
        return data

