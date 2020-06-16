import time
import json
from multiprocessing import Queue
from legimens import Object, App
from legimens.Object import ref

# - logging config
import sys
from loguru import logger as log
log.remove()
log.add(sys.stderr, level='TRACE')
# -

import trio

from utils.websocket_client import send_iter, listener_process

addr, port = '127.0.0.1', 8082

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


def test_with_coro__resetting():

    app = App(addr=addr, port=port)
    client = LeClient('value')
    try:
        app.run()
        time.sleep(.05)
        object = []
        async def watch():
            app.vars.value = object
            await trio.sleep(.05)
        app.add_coroutine(watch)

        app.vars.value = object
        _ = client.start(f'ws://{addr}:{port}')
        for i in range(5):
            object.append(i)
            time.sleep(.1)

        time.sleep(.1)

        assert client.updates_count() > 0
        responses = client.get_all_updates()
        last_msg = responses[-1]
        last_upd = json.loads(last_msg)
        assert last_upd['value'] == object

    finally:
        app.stop()

