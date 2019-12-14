import multiprocessing as thr
import json
import time
from utils.websocket_client import send_iter_sync, send_iter
from hosta import Hobject, Happ

def test_create():
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

    addr, port = '127.0.0.1', 8080
    app = Happ(addr=addr, port=port)
    app.vars.users = [u, User(name='Mohn', age=10)]
    app.vars.title = 'Test'
    #app.run()
    p = thr.Process(target=app.run, args=())
    p.start()
    time.sleep(.1)

    async def iter(ws):
        msg = await ws.get_message()
        root_id = msg
        print('root_id', root_id)
        async def get_obj(ws):
            user = await ws.get_message()
            print('user', user)
            yield ''
        await send_iter(f'ws://{addr}:{port}/{root_id}',get_obj)
        yield ''
        return


    p1= thr.Process(target=send_iter_sync, args=(f'ws://{addr}:{port}',iter))
    p2= thr.Process(target=send_iter_sync, args=(f'ws://{addr}:{port}',iter))
    p1.start()
    p2.start()
    p1.join()
    p.terminate()
    p.join()

