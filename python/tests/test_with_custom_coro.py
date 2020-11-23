import time
import json
from legimens import Object, App
from legimens.Object import ref
from LeClient import LeClient

import trio

addr, port = '127.0.0.1', 7082

def test_with_coro__resetting():
    app = App(addr=addr, port=port, log_level='TRACE')
    client = LeClient()
    try:
        app.run()
        time.sleep(.05)
        object = []
        async def watch():
            while True:
                app.vars.value = object
                await trio.sleep(.05)
        app.schedule_coroutine(watch)

        app.vars.value = object
        _ = client.start(f'ws://{addr}:{port}')
        for i in range(20):
            object.append(i)
            time.sleep(.02)

        time.sleep(.4)

        assert client.updates_count() > 0
        responses = client.get_all_updates()
        last_msg = responses[-1]
        last_upd = json.loads(last_msg)
        assert last_upd['value'] == object

    finally:
        app.stop()

