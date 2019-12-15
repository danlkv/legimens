import multiprocessing.dummy as thr
from collections import defaultdict
import trio
import json
from loguru import logger as log

from hosta import Hobject
from hosta.helpers.dictMap import obj_map
from hosta.websocket.server import start_server

def ref(obj):
    return repr(obj)

class Happ:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.vars = Hobject()
        self._child_obj = {}
        self._subscr = defaultdict(lambda: [], {})
        self._cancel_scope = trio.CancelScope()
        self._running = True

        self._on_val_set(None,self.vars)

    def _register_child(self, o):
        if isinstance(o, Hobject):
            o.subscribe_set(self._on_val_set)
            self._child_obj[ref(o)] = o
            log.debug("Added child object {}", o)
            # returning none makes mapper
            # traverse the whole dict tree 
            return None

    def _on_val_set(self, name, value):
        obj_map(value, self._register_child)

    def _ser_vars(self):
        return json.dumps(self.vars)

    async def _handler(self, ws):
        try:
            log.info(f"New connection from {ws.path}")
            refv = ws.path.split('/')[1]
            log.debug(f"Children {self._child_obj}")
            log.debug(f"Subscribers {self._subscr}")
            # if anything is in the path
            if len(refv)>0:
                # Subscribe this client to monitor vars
                self._subscr[refv].append( ws )
                # send the current object to it
                child = self._child_obj[refv]
                # if updates to other clients sent, 
                # Initiate state for current cliet
                if not child._touched:
                    yield child.serial()

                while True:
                    msg = await ws.get_message()
                    child.inbound = msg
                yield None
                await trio.sleep_forever()

            else:
                yield ref(self.vars)
        except Exception as e:
            log.error(e)

    async def _monitor_vars(self):
        while True:
            for ref in self._child_obj:
                listeners  = self._subscr[ref]
                alive = [ws for ws in listeners if not ws.closed]
                self._subscr[ref] = alive
                listeners = alive
                if len(listeners) > 0:
                    child = self._child_obj[ref]
                    if child._touched:
                        message = child.serial()
                        try:
                            for ws in listeners:
                                await ws.send_message(message)
                            child._mark_untouched()
                        except Exception as e:
                            log.error("Error sending update to {}: {}", ws, e)

            if not self._running:
                self._cancel_scope.cancel()

            await trio.sleep(.2)

    async def _start(self):
        with self._cancel_scope:
            args = (self.addr, self.port, self._handler)
            async with trio.open_nursery() as nursery:
                nursery.start_soon(start_server, *args+(nursery,))
                nursery.start_soon(self._monitor_vars)
        log.info("App stopped")

    def run_sync(self):
        trio.run(self._start)

    def run(self):
        t = thr.Process(target=trio.run, args=(self._start,))
        t.start()
        return t
    def stop(self):
        self._running = False

