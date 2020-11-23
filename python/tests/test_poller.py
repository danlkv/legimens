import time
import json
from multiprocessing import Queue
from legimens import Object, App
from legimens.Object import ref
from LeClient import LeClient

from utils.websocket_client import send_iter, listener_process

addr, port = '127.0.0.1', 7082

def test_simple_var_poll():
    responses = Queue()


    app = App(addr=addr, port=port)
    client = LeClient('value')
    try:
        app.run()
        time.sleep(.05)
        class List(list):
            pass
        object = List()
        app.watch_obj(object)
        app.vars.value = ref(object)
        _ = client.start(f'ws://{addr}:{port}')
        for i in range(5):
            object.append(i)
            time.sleep(.1)

        time.sleep(.1)
        assert client.updates_count() > 0
        responses = client.get_all_updates()
        assert responses[-1] == str(object)

    finally:
        app.stop()


def test_object_poll():
    responses = Queue()


    app = App(addr=addr, port=port)
    client = LeClient('rapid_updated')

    try:
        app.run()
        time.sleep(.05)
        _ = client.start(f'ws://{addr}:{port}')

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

        responses = [json.loads(x) for x in client.get_all_updates()]
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

