import time
import json
from multiprocessing import Queue
from legimens import Object, App
from legimens.Object import ref

from utils.websocket_client import send_iter, listener_process

addr, port = '127.0.0.1', 8082

def test_object_poll():
    responses = Queue()

    async def init(ws):
        msg = await ws.get_message()
        root_id = json.loads(msg)['root']
        print('<<<root_id<<<', root_id)

        async def root_iter(ws):
            root = await ws.get_message()
            root = json.loads(root)
            updater = root['rapid_updated']
            async def listen_upd(ws):
                while True:
                    x = json.loads(await ws.get_message())
                    responses.put(x)
                yield
            await send_iter(f'ws://{addr}:{port}/{updater}', listen_upd)
            yield

        await send_iter(f'ws://{addr}:{port}/{root_id}',root_iter)
        yield None
        return

    app = App(addr=addr, port=port)
    p1 = listener_process(f'ws://{addr}:{port}', init)
    try:
        app.run()
        time.sleep(.05)
        p1.start()

        class Rollin(Object):
            def __init__(self):
                super().__init__()
                self.x = []

        rapid = Rollin()
        app.watch_obj(rapid)
        app.vars.rapid_updated = ref(rapid)

        dt = 1e-4
        T = 0.5
        # Put data in bursts, use N appends between sleeps
        N = int(0.005/dt)
        app._watch_poll_delay = 0.1
        for i in range(int(T//dt)):
            rapid.x += [i]
            if i%N==0:
                #print('put',i, time.time())
                # Don't try to do μs delays, need Real-Time OS for this
                time.sleep(N*dt)

        #Wait for finish update
        time.sleep(app._watch_poll_delay)

        responses = [responses.get() for _ in range(responses.qsize())]
        assert responses
        xlens = [len(x['x']) for x in responses]
        assert xlens[-1] == int(T//dt)
        print("Lengths of rapid updates of growing list", xlens)
        assert len(responses) >= T//app._watch_poll_delay
        dlens = [x1-x0 for x0, x1 in zip(xlens[:-1], xlens[1:])]
        incrs = app._watch_poll_delay/dt
        print(f"Lengths increments: should be near {incrs}", dlens)
        assert all(x <= incrs for x in dlens)

    finally:
        app.stop()

test_object_poll()
