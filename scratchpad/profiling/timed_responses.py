from trio_websocket import serve_websocket
from trio_websocket import ConnectionClosed as TrioConnClose
import trio
import asyncio, websockets
from multiprocessing.dummy import Process as Thread

## ## Wrappers for different backends

def trio_handler_wrapper(func):
    async def handler(request):
        try:
            ws = await request.accept()
            ws.recv = ws.get_message
            ws.send = ws.send_message
            await func(ws, path=ws.path)
        except TrioConnClose:
            print('trio end conn')
            return
    return handler

def asyncio_handler_wrapper(func):
    async def handler(ws, path):
        try:
            await func(ws, path=path)
        except websockets.exceptions.ConnectionClosedError:
            print('asyncio end conn')

    return handler

## ## <

class wsTrio():
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self._cancel_scope = trio.CancelScope()

    def _in_thread(self):
        async def serve():
            with self._cancel_scope:
                async with trio.open_nursery() as nursery:
                    await serve_websocket(
                        self.handler,
                        self.addr, self.port,
                        ssl_context=None,
                        handler_nursery=nursery
                    )
        trio.run(serve)

    def start(self):
        self.thread = Thread(target=self._in_thread)
        self.thread.start()

    def stop(self):
        self._cancel_scope.cancel()


class wsAsyncio():
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self._cancel_scope = trio.CancelScope()

    def _in_thread(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        serve = websockets.serve(self.handler, self.addr, self.port)
        self.serv = asyncio.get_event_loop().run_until_complete(serve)
        print('async run')
        asyncio.get_event_loop().run_forever()
        print('exited ws worker')

    def start(self):
        self.thread = Thread(target=self._in_thread)
        self.thread.start()

    def stop(self):
        self.serv.close()

async def echo(ws, path):
    print('Connection')
    i = 0
    while True:
        m = await ws.recv()
        i+=1
        if 'exit' in m :return
        print('s:', i, m)
        await ws.send(m)



print('run')

ss = wsAsyncio('localhost', 7000)
ss.handler = asyncio_handler_wrapper(echo)
ss.start()

ts = wsTrio('localhost', 7001)
ts.handler = trio_handler_wrapper(echo)
ts._in_thread()
ts.start()
print('started ts')
ts.thread.join()
ss.thread.join()
