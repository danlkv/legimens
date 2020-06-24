
from multiprocessing import Queue
from utils.websocket_client import send_iter, listener_process
import json

# Implementation of Legimens client
class LeClient:
    """
    Listens for updates of `name` variable and
    allows to yield updates for it
    """
    def __init__(self, name, on_connect=None):
        self.on_connect = on_connect or self.listen_upd
        self.name = name
        self.updates_queue = Queue()

    async def _start_comm(self, ws):
        """ Connects to / and gets root id. """
        # First, get the root id of variables
        msg = await ws.get_message()
        root_id = json.loads(msg)['root']
        print('<<<root_id<<<', root_id)
        # Conect to root and get variable ref id
        await send_iter(f'{self.addr}/{root_id}', self.on_connect)
        yield None
        return

    async def listen_upd(self, ws):
        while True:
            x = await ws.get_message()
            print('<<msg<<', x)
            self.updates_queue.put(x)
        yield

    def iter_updates(self):
        return iter(self.updates_queue.get, None)

    def get_all_updates(self):
        N = self.updates_count()
        responses = [self.updates_queue.get() for _ in range(N)]
        return responses

    def updates_count(self):
        return self.updates_queue.qsize()

    def start(self, addr):
        self.addr = addr
        p1 = listener_process(addr, self._start_comm)
        p1.start()
