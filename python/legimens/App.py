from threading import Thread
from collections import defaultdict
import trio
import time
import sys
import weakref
import json
from loguru import logger as log
log.remove()
log.add(sys.stdout, level="DEBUG")


from legimens import Object
from legimens.Object import ref
from legimens.helpers.dictMap import obj_map
from legimens.websocket.server import start_server

class App:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.vars = Object()
        self._child_obj = weakref.WeakValueDictionary()
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

            o.subscribe_set(put_updates)
            o.subscribe_set(register_new)

            self._child_obj[ref(o)] = o
            log.debug("Added child object {} with ref {}", o, ref(o))
            # returning none makes mapper
            # traverse the whole dict tree 
            return None

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

    async def _monitor_updates(self):
        while True:
            for ref_ in self._children_updates:
                # Clean listeners that are dead
                listeners = self._get_alive_listeners(ref_)
                self._subscr[ref_] = listeners
                if len(listeners) > 0:
                    await self._send_updates_to_listeners(ref_, listeners)


            await trio.sleep(.02)

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

    def _get_alive_listeners(self, ref):
        listeners  = self._subscr[ref]
        return [ ws for ws in listeners if not ws.closed]

## ## ## ## ## ## Starting ## ## ## ## ## ## 

    async def _start(self):
        args = (self.addr, self.port, self._handler)
        try:
            async with trio.open_nursery() as nursery:
                self._cancel_scope = nursery.cancel_scope
                nursery.start_soon(self._watch_for_cancel)
                nursery.start_soon(start_server, *args+(nursery,))
                nursery.start_soon(self._monitor_updates)
        except Exception:
            self._running = False
            log.info("App crashed.")
            raise
        log.info("App stopped")

    def run_sync(self):
        trio.run(self._start)

    def run(self):
        t = Thread(target=trio.run, args=(self._start,))
        t.start()
        time.sleep(.05)
        if not self._running:
            raise Exception("Failed to start Legimens")
        return t

## ## ## ## ## ## Stopping ## ## ## ## ## ## 

    async def _watch_for_cancel(self):
        """
        It's a good question how often we should
        check whether `stop()` was called. Use 0.2seconds for now
        """
        while True:
            if not self._running:
                log.debug("Cancelling trio scope")
                self._cancel_scope.cancel()
            await trio.sleep(.2)

    def stop(self):
        """ set `self._running` to False,
        trio coro that runs in another thread will find it and call
        `self._cancel_scope.cancel()`

        To determine whether the main nursery was cancelled,
        repeatedly checks for `self._cancel_scope.cancelled_caught`.
        Shouldn't take more than 2seconds, otherwise is a bug
        """
        self._running = False
        for _ in range(20):
            time.sleep(.1)
            if self._cancel_scope.cancelled_caught:
                return
        log.error("Stopping failed. This is probably a bug, please report it.")
