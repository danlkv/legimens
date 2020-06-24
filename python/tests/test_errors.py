import time
import json
from legimens import Object, App
from legimens.Object import ref
from LeClient import LeClient

import trio

addr, port = '127.0.0.1', 8082

def test_non_json_serializable():
    app = App(addr=addr, port=port, log_level='TRACE')
    client = LeClient('value')
    try:
        app.run()
        time.sleep(.05)
        class NonSerializable:
            value = 1
        object = NonSerializable()

        app.vars.value = object

        _ = client.start(f'ws://{addr}:{port}')
        for i in range(5):
            object.value = i
            time.sleep(.02)

        good_value = 'Good value'
        app.vars.value = good_value

        time.sleep(.1)

        assert client.updates_count() > 0
        responses = client.get_all_updates()
        last_msg = responses[-1]
        last_upd = json.loads(last_msg)
        assert last_upd['value'] == good_value

    finally:
        app.stop()

