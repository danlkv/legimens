import time
import json
from legimens import Object, App
from legimens.Object import ref
from legimens import Watcher
from LeClient import LeClient

import trio

addr, port = '127.0.0.1', 7082

def test_watcher_simple():
    app = App(addr=addr, port=port, log_level='TRACE')
    client = LeClient()
    watcher = Watcher(app, delay=0.3)
    try:
        app.run()
        time.sleep(.05)
        object = []
        watcher.bind(app.vars, 'value', object)

        _ = client.start(f'ws://{addr}:{port}')
        for i in range(20):
            object.append(i)
            time.sleep(.05)

        time.sleep(.5)

        assert client.updates_count() > 0
        responses = client.get_all_updates()
        last_msg = responses[-1]
        last_upd = json.loads(last_msg)
        assert last_upd['value'] == object

    finally:
        app.stop()

def test_watcher_nested():
    app = App(addr=addr, port=port, log_level='TRACE')
    client = LeClient('granny.mommy')
    watcher = Watcher(app, delay=0.3)
    try:
        app.run()
        time.sleep(.05)
        granny = Object()
        mommy = Object()
        granny.mommy = mommy
        PKEY = 'buddy'
        buddy = []
        watcher.bind(mommy, PKEY, buddy)
        app.vars.granny = granny

        _ = client.start(f'ws://{addr}:{port}')
        for i in range(20):
            buddy.append(i)
            time.sleep(.05)

        time.sleep(.5)

        assert client.updates_count() > 0
        responses = client.get_all_updates()
        last_msg = responses[-1]
        last_upd = json.loads(last_msg)
        assert last_upd[PKEY] == buddy

    finally:
        app.stop()

