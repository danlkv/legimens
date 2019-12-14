from trio_websocket import open_websocket_url, ConnectionClosed
import trio
from sys import stderr

async def send_iter(addr, iterable):
    try:
        async with open_websocket_url(addr) as ws:
            try:
                async for message in iterable(ws):
                    if message is not None:
                        await ws.send_message(message)
            except StopIteration:
                print("Closing connection")
                return
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)
    except ConnectionClosed as e:
        print(f'Connection to {addr} closed',e)

def send_iter_sync(addr, iterable):
    return trio.run(send_iter, addr, iterable)
