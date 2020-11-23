
from multiprocessing import Queue
from utils.websocket_client import send_iter, listener_process
import json


class LeClient:
    """
    Finds variable by path from name and listens to updates and
    allows to yield updates for it
    """
    def __init__(self, name=None, communicator=None):
        """
        Communicate with LeObject in this way:

            def ping_pong_communicator(self):
                inp = yield
                while True:
                    if inp == 'Ping':
                        inp = yield 'Pong'
                    else:
                        inp = yield 'Ping'

        Args:
            name (str): name of attribute or dot-divided path in hierarchy of LeObjects
            communicator (generator): generator with in_message = yield out_message
        """
        self.communicator = communicator
        if name:
            self.path = name.split('.')
        else:
            self.path = []
        self.path_ix = 0
        self.updates_queue = Queue()

    async def _start_comm(self, ws):
        """ Connects to / and gets root id. """
        # First, get the root id of variables
        msg = await ws.get_message()
        root_id = json.loads(msg)['root']
        print('<<<root_id<<<', root_id)
        # Conect to root and get variable ref id
        await send_iter(f'{self.addr}/{root_id}', self.listen_upd)
        yield None
        return

    async def listen_upd(self, ws):
        # -- determine next index
        x_init = await ws.get_message()
        print('<<msg<<', x_init[:200])

        try:
            next_key = self.path[self.path_ix]
            x = json.loads(x_init)
            next_ref = x[next_key]
            self.path_ix += 1
            print(f'><><LeClient: next ref {next_ref} from {next_key}')
            await send_iter(f'{self.addr}/{next_ref}', self.listen_upd)
        except IndexError:
            # Reached end of path, start listening to updates
            print('<><>LeClient: found target!')
            self.updates_queue.put(x_init)
            while True:
                x = await ws.get_message()
                print('<<msg<<', x[:200])
                if self.communicator:
                    ret = self.communicator.send(x)
                    if ret is not None:
                        print('>>upd>>', ret)
                        yield ret
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
