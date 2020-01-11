from multiprocessing import Process, Queue
import json
import time
from utils.websocket_client import send_iter_sync, send_iter
from legimens import Object, App
from legimens.Object import serial
addr, port = '127.0.0.1', 8082

def setup():
    class User(Object):
        def __init__(self, name, age):
            super().__init__()
            self.name = name
            self.age = age
    class Post(Object):
        def __init__(self, title, comments=[]):
            super().__init__()
            self.title = title
            self.comments = comments
    u = User(name='John', age=30)
    u.posts = [Post(title='Legi'), Post(title='Megi')]

    app = App(addr=addr, port=port)
    app.vars.users = [u, User(name='Mohn', age=10)]
    app.vars.title = 'Test'
    return app

def test_create():
    responses = Queue()

    async def init(ws):
        msg = await ws.get_message()
        root_id = msg
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

    app = setup()
    p1 = Process(target=send_iter_sync, args=(f'ws://{addr}:{port}',init))
    p2 = Process(target=send_iter_sync, args=(f'ws://{addr}:{port}',init))

    app.run()
    time.sleep(.2)

    p1.start()
    p2.start()

    time.sleep(.15)
    assert responses.qsize()==2
    for _ in range(2):
        assert responses.get() == serial(dict(app.vars))

    app.vars.title = 'Changed title'
    time.sleep(.05)

    assert responses.qsize()==2
    for _ in range(2):
        r = json.loads(responses.get())
        assert r['title']  == app.vars.title

    app.stop()
    p1.join()
    p2.join()
