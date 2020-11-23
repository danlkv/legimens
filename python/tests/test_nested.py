from multiprocessing import Queue
import json
import time
from utils.websocket_client import send_iter, listener_process
from setup_app import setup_app_nested
from legimens.Object import serial
from loguru import logger as log

addr, port = '127.0.0.1', 7082

def test_nested():
    responses = Queue()

    async def init(ws):
        msg = await ws.get_message()
        root_id = json.loads(msg)['root']
        print('<<<root_id<<<', root_id)

        async def root_iter(ws):
            async def listen_user(ws):
                msg = await ws.get_message()
                print('<<<<User<<<<<', msg)
                responses.put(json.loads(msg))
                msg = await ws.get_message()
                upd = json.loads(msg)
                responses.put(upd)
                print('<<<question:<<<<', upd['question'])
                yield json.dumps({'answer': 42})

            i = 0
            while True:
                root = await ws.get_message()
                responses.put(root)
                print('<<<<root_obj<<<<<', root)
                time.sleep(.02)
                if i==0:
                    root = json.loads(root)
                    user_ref = root['users'][0]
                    await send_iter(f'ws://{addr}:{port}/{user_ref}',listen_user)
                yield None
                i+=1

        await send_iter(f'ws://{addr}:{port}/{root_id}',root_iter)
        yield None
        return

    app = setup_app_nested(addr, port)
    p1 = listener_process(f'ws://{addr}:{port}', init)
    p2 = listener_process(f'ws://{addr}:{port}', init)

    try:
        app.run()
        time.sleep(.05)

        p1.start()
        p2.start()

        time.sleep(.4)
        assert responses.qsize()==4
        for _ in range(2):
            assert responses.get() == json.dumps(serial(dict(app.vars)))

        for _ in range(2):
            u = responses.get()
            assert u['age'] == app.vars.users[0].age

        app.vars.users[0].question = 'Meaning of the world'
        time.sleep(.1)

        assert responses.qsize()==2
        for _ in range(2):
            updates = responses.get()
            assert updates['question'] == 'Meaning of the world'
            assert app.vars.users[0].answer == 42

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


