import multiprocessing.dummy as thr
from collections import defaultdict
import trio
import sys
import gc
import json
from loguru import logger as log
log.remove()
log.add(sys.stdout, level="INFO")


from legimens import Object
from legimens.Object import ref
from legimens.helpers.dictMap import obj_map
from legimens.websocket.server import start_server

class App:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.vars = Object()
        self._child_obj = {}
        self._children_updates = defaultdict(dict, {})
        self._subscr = defaultdict(list, {})
        self._cancel_scope = trio.CancelScope()
        self._running = True

        self._register_child(self.vars)

    def _register_child(self, o):
        if isinstance(o, Object):

            def put_updates(name, value):
                """ Put the updates to temp dictionary """
                name, value = o._prepare_send(name, value)
                self._children_updates[ref(o)].update({name:value})

            def register_new(name, value):
                """ Make `Object` children of this Object also be listened """
                obj_map(value, self._register_child)
                self._clean_children()

            o.subscribe_set(put_updates)
            o.subscribe_set(register_new)

            self._child_obj[ref(o)] = o
            log.debug("Added child object {} with ref {}", o, ref(o))
            # returning none makes mapper
            # traverse the whole dict tree 
            return None

    def _clean_children(self):
        """ If one of our children in _child_obj has
        only one referrer, this means that this object exists only
        in _child_obj and thus is no longer needed by user

        Note: this function is called  before actual set value.
        This means that we will always have one object left
        TODO: fix described above
        """
        refcnts = { k:len(gc.get_referrers(v)) for k, v in self._child_obj.items() } 
        log.debug(f"Children ref counts: {refcnts}")
        to_delete = []
        for k, v in refcnts.items():
            if v <= 3:
                to_delete.append(k)
        log.debug(f"Children for deletion: {to_delete}")
        for k in to_delete:
            del self._child_obj[k]
            del self._subscr[k]
            del self._children_updates[k]

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
                yield json.dumps({'root':ref(self.vars)})
        except Exception as e:
            log.error("Handling {} error:{}", type(e), e)

    async def _handle_obj_ref(self, ws, ref):
        # Subscribe this client to monitor vars
        # send the current object to it
        child = self._child_obj.get(ref)
        if child is None:
            log.error("No child with ref {}", ref)
            return

        self._subscr[ref].append( ws )

        # if updates to other clients sent, 
        # Initiate state for current cliet
        if not self._children_updates[ref]:
            x = {}
            for name, value in child.items():
                name, value = child._prepare_send(name, value)
                x[name] = value
            log.info("Yield initial update {}",x.keys())
            yield json.dumps(x)

        await self._child_updating_loop(ws, child)

        yield None

    async def _child_updating_loop(self, ws, child):
        log.debug("Listening for updates for {}", ref(child))
        while True:
            msg = await ws.get_message()
            try:
                updates = json.loads(msg)
                log.debug("Updates for {} : {}", ref(child), updates)
                for key, value in updates.items():
                    child._commit_update(key, value)
            except json.JSONDecodeError:
                log.error("JSON decode error: {}", msg)

## ## ## ## ## ## Serving updates ## ## ## ## ## ## 

    def _get_alive_listeners(self, ref):
        listeners  = self._subscr[ref]
        return [ ws for ws in listeners if not ws.closed]

    async def _send_updates_to_listeners(self, ref, listeners):
        updates = self._children_updates[ref]
        if not updates: return
        message = json.dumps(updates)
        try:
            for ws in listeners:
                await ws.send_message(message)
                self._children_updates[ref] = {}
        except Exception as e:
            log.error("Error sending update to {}: {}", ws, e)

    async def _monitor_vars(self):
        while True:
            for ref_ in self._children_updates:
                # Clean listeners that are dead
                listeners = self._get_alive_listeners(ref_)
                self._subscr[ref_] = listeners
                if len(listeners) > 0:
                    await self._send_updates_to_listeners(ref_, listeners)

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

