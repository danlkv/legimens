import multiprocessing as thr
import json
import time
from utils.websocket_client import send_iter_sync, send_iter
from hosta import Hobject, Happ
addr, port = '127.0.0.1', 8080

def setup():
    class User(Hobject):
        def __init__(self, name, age):
            super().__init__()
            self.name = name
            self.age = age
    class Post(Hobject):
        def __init__(self, title, comments=[]):
            super().__init__()
            self.title = title
            self.comments = comments
    u = User(name='John', age=30)
    u.posts = [Post(title='Happ'), Post(title='Mapp')]

    app = Happ(addr=addr, port=port)
    app.vars.users = [u, User(name='Mohn', age=10)]
    app.vars.title = 'Test'
    return app

def test_create():
    app = setup()
    app.run()
    time.sleep(.1)

    async def init(ws):
        msg = await ws.get_message()
        root_id = msg
        print('root_id', root_id)
        async def root_iter(ws):
            while True:
                root = await ws.get_message()
                print('<<<<root<<<<<', root)
                yield None
        await send_iter(f'ws://{addr}:{port}/{root_id}',root_iter)
        yield None
        return


    p1= thr.Process(target=send_iter_sync, args=(f'ws://{addr}:{port}',init))
    p2= thr.Process(target=send_iter_sync, args=(f'ws://{addr}:{port}',init))
    p1.start()
    p2.start()
    time.sleep(.2)
    app.vars.title = 'Changed title'
    time.sleep(.2)
    p1.join()

    app.stop()
