import multiprocessing.dummy as thr
from collections import defaultdict
import trio
import sys
import gc
import pprint
import json
from loguru import logger as log
log.remove()
log.add(sys.stdout, level="INFO")


from hosta import Hobject
from hosta.Hobject import ref
from hosta.helpers.dictMap import obj_map
from hosta.websocket.server import start_server

class Happ:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.vars = Hobject()
        self._child_obj = {}
        self._subscr = defaultdict(list, {})
        self._cancel_scope = trio.CancelScope()
        self._running = True

        self._on_val_set(None,self.vars)

    def _register_child(self, o):
        if isinstance(o, Hobject):
            o.subscribe_set(self._on_val_set)
            self._child_obj[ref(o)] = o
            log.debug("Added child object {} with ref {}", o, ref(o))
            # returning none makes mapper
            # traverse the whole dict tree 
            self._clean_children()
            return None
    
    def _on_val_set(self, name, value):
        obj_map(value, self._register_child)

    def _clean_children(self):
        """ If one of our children in _child_obj has
        only one referrer, this means that this object exists only
        in _child_obj and thus is no longer needed by user

        Note: this function is called  before actual set value.
        This means that we will always have one object left
        TODO: fix described above
        """
        refcnts = { k:gc.get_referrers(v) for k, v in self._child_obj.items() } 
        refcnts = { k:(len(v)) for k, v in refcnts.items()}
        log.debug(f"Children ref counts: {refcnts}")
        to_delete = []
        for k, v in refcnts.items():
            if v<2:
                to_delete.append(k)
        log.debug(f"Children for deletion: {to_delete}")
        for k in to_delete:
            del self._child_obj[k]
            del self._subscr[k]

    def _ser_vars(self):
        return json.dumps(self.vars)

## ## ## ## ## ## Listening updates ## ## ## ## ## ## 

    async def _handler(self, ws):
        try:
            if hasattr(ws.remote, 'address'): ip = ws.remote.address
            else: ip = ws.remote
            log.info(f"New ws connection of {ws.path} from {ip}")
            log.debug(f"Children objects: {self._child_obj.keys()}")
            log.debug(f"Clients connected: {self._subscr}")

            refv = ws.path.split('/')[1]
            # if anything is in the path
            if len(refv)>0:
                async for msg in self._handle_obj_ref(ws, refv):
                    yield msg

            else:
                # return link to root element
                log.info(f"Sending root {ref(self.vars)}")
                yield ref(self.vars)
        except Exception as e:
            log.error("Handling {} error:{}", type(e), e)

    async def _handle_obj_ref(self, ws, ref):
        # Subscribe this client to monitor vars
        self._subscr[ref].append( ws )
        # send the current object to it
        child = self._child_obj[ref]
        # if updates to other clients sent, 
        # Initiate state for current cliet
        if not child._touched:
            log.info("Yield initial update")
            yield child.serial()

        await self._child_updating_loop(ws, child)

        yield None
        # save ws connection open
        await trio.sleep_forever()

    async def _child_updating_loop(self, ws, child):
        log.debug("Listening for updates for {}", ref(child))
        while True:
            msg = await ws.get_message()
            try:
                updates = json.loads(msg)
                log.debug("Updates for {} : {}", ref(child), updates)
                child.update( updates )
                child._touched = True
            except json.JSONDecodeError:
                log.error("JSON decode error: {}", msg)

## ## ## ## ## ## Serving updates ## ## ## ## ## ## 

    def _get_alive_listeners(self, ref):
        listeners  = self._subscr[ref]
        return [ ws for ws in listeners if not ws.closed]

    async def _send_child_to_listeners(self, child, listeners):
        message = child.serial()
        try:
            for ws in listeners:
                await ws.send_message(message)
            child._mark_untouched()
        except Exception as e:
            log.error("Error sending update to {}: {}", ws, e)

    async def _monitor_vars(self):
        while True:
            for r in self._child_obj:
                alive = self._get_alive_listeners(r)
                self._subscr[r] = alive
                listeners = alive
                if len(listeners) > 0:
                    child = self._child_obj[r]
                    if child._touched:
                        await self._send_child_to_listeners(child, listeners)

            if not self._running:
                self._cancel_scope.cancel()

            await trio.sleep(.02)

## ## ## ## ## ## Starting ## ## ## ## ## ## 

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

## ## ## ## ## ## Stopping ## ## ## ## ## ## 

    def stop(self):
        self._running = False

