import trio
from trio_websocket import serve_websocket, ConnectionClosed
from loguru import logger as log

PORT_RETRIES = 5 #handle port in use: not used

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

    for i in range(PORT_RETRIES+1):  #handle port in use: not used
        try:
            await serve_websocket(server, addr, port,
                                  ssl_context=None,
                                  handler_nursery=nursery)
            break
        except OSError as ose:
            #
            # Handling port in use produces a problem when you don't know where to connect in front.
            # Let's better fail.
            #
            log.error(f"Websocket start on {port} failed: {ose}")
            raise

            #   if ose.args[0] != 98:
            #       log.error(f"Websocket start on {port} failed: {ose}")
            #       raise
            # --#handle port in use: not used
            log.warning(f"Port {port} is already in use")
            if i == PORT_RETRIES:
                log.error(f"Failed to start websocket after {PORT_RETRIES} attempts to find an open port.")
                raise
            log.info(f"Trying to start websocket on {addr}:{port+1}...")
            await ws_serve(addr, port+1, iterable_fn, nursery=nursery)
            # --#handle port in use: not used
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

