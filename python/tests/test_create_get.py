from multiprocessing import Process, Queue
import json
import time
from utils.websocket_client import send_iter_sync, send_iter
from setup_app import setup_app
from legimens.Object import serial
from loguru import logger as log

addr, port = '127.0.0.1', 8082

def listener_process(url, generator):
    p = Process(target=(send_iter_sync), args=(url,generator))
    p.daemon = True
    return p

def test_basic():
    responses = Queue()

    async def init(ws):
        msg = await ws.get_message()
        root_id = json.loads(msg)['root']
        print('<<<root_id<<<', root_id)

        async def root_iter(ws):
            while True:
                root = await ws.get_message()
                print('<<<<root_obj<<<<<', root)
                responses.put(root)
                yield None

        await send_iter(f'ws://{addr}:{port}/{root_id}',root_iter)
        yield None
        return

    app = setup_app(addr, port)
    p1 = listener_process(f'ws://{addr}:{port}', init)
    p2 = listener_process(f'ws://{addr}:{port}', init)

    try:
        app.run()
        time.sleep(.05)

        p1.start()
        p2.start()

        time.sleep(.15)
        assert responses.qsize()==2
        for _ in range(2):
            assert responses.get() == json.dumps(serial(dict(app.vars)))

        app.vars.title = 'Changed title'
        time.sleep(.05)

        assert responses.qsize()==2
        for _ in range(2):
            r = json.loads(responses.get())
            assert list(r.keys()) == ['title']
            assert r['title']  == app.vars.title

    finally:
        print(':: Stopping app ::')
        app.stop()
