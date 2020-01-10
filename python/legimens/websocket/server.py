import trio
from trio_websocket import serve_websocket, ConnectionClosed
from loguru import logger as log

class StopServer(Exception):
    pass

async def ws_serve(addr, port, iterable_fn, nursery=None):
    async def server(request):
        try:
            ws = await request.accept()

            try:
                async for message in iterable_fn(ws):
                    if message is not None:
                        await ws.send_message(message)
            except StopIteration:
                log.info("Closing connection")
        except ConnectionClosed as e:
            log.warning(f"Connection closed by remote: {e}")
            return
    try:
        await serve_websocket(server, addr, port,
                              ssl_context=None,
                              handler_nursery=nursery)
    except OSError as ose:
        log.error(f"Websocket start on {port} failed: {ose}")
        raise
        return
    log.info("Websocket terminates")

async def start_server(addr, port, handler_func=print, nursery=None):
    log.info(f"Starting ws server at {addr}:{port}")
    await ws_serve(addr, port, handler_func, nursery=nursery)

def start_server_sync(addr, port, handler_func=print):
    trio.run(start_server, addr, port, handler_func)

def start_server_handler(addr, port, handler_func):
    async def handler(client_messages):
        async for message in client_messages:
            yield str(handler_func(message))
    start_server_sync(addr, port, handler)

def stop():
    print("You found a stub!")

def main():
    start_server_sync('127.0.0.1',8000)

if __name__=='__main__':
    main()

