from hosta.websocket.server import start_server
import multiprocessing.dummy as thr
from collections import defaultdict
import gc
import trio
import sys
from hosta import Hobject
import json
from loguru import logger as log

def ref(obj):
    return repr(obj)

class Happ:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.vars = Hobject()
        self.vars.subscribe_set(self._on_val_set)
        self._child_obj = {}
        self._subscr = defaultdict(lambda: [], {})
        self._on_val_set('v',self.vars)
        log.info(f"Refs {sys.getrefcount(self.vars)}")
        log.info(f"Refs {gc.get_referrers(self.vars)}")
        self._cancel_scope = trio.CancelScope()
        self._running = True

    def _add_hobject(self, hobject):
        self._child_obj[ref(hobject)] = hobject
        print("Added child object",hobject)
        for child in hobject._get_child_obj():
            print("Added child objec",hobject)
            self._child_obj[ref(child)] = child
            child.subscribe_set(self._on_val_set)
        hobject.subscribe_set(self._on_val_set)

    def _on_val_set(self, name, value):
        print("on_val_set", name, value, type(value))
        if isinstance(value, Hobject):
            self._add_hobject(value)
        if isinstance(value, list):
            print("List")
            [self._on_val_set('iterm',x) for x in value]
        print("Done")

    def _ser_vars(self):
        return json.dumps(self.vars)

    async def _handler(self, ws):
        try:
            log.info(f"New connection from {ws.path}")
            refv = ws.path.split('/')[-1]
            log.info(f"Ref {refv}")
            log.info(f"Children {self._child_obj}")
            if len(refv)>0:
                # Subscribe this websocket to monitor vars
                self._subscr[refv].append( ws )
                yield None
                await trio.sleep(.5)

            else:
                yield ref(self.vars)
        except Exception as e:
            log.error(e)

    async def _monitor_vars(self):
        while True:
            for ref in self._child_obj:
                listeners  = self._subscr[ref]
                if len(listeners) > 0:
                    child = self._child_obj[ref]
                    if child._touched:
                        for ws in listeners:
                            message = child.serial()
                            try:
                                await ws.send_message(message)
                                child._mark_untouched()
                            except Exception as e:
                                log.error("Error sending update to %s", ws)
                    else:
                        log.debug("Child {} not touched", ref)
                else:
                    log.debug("No listeners for {}", ref)

            if not self._running:
                self._cancel_scope.cancel()

            await trio.sleep(.1)

    async def _start(self):
        with self._cancel_scope:
            args = (self.addr, self.port, self._handler)
            async with trio.open_nursery() as nursery:
                nursery.start_soon(start_server, *args+(nursery,))
                nursery.start_soon(self._monitor_vars)
        print("1")

    def run_sync(self):
        trio.run(self._start)

    def run(self):
        t = thr.Process(target=trio.run, args=(self._start,))
        t.start()
        return t
    def stop(self):
        self._running = False

