from threading import Thread
from collections import defaultdict
import trio
import time
import sys
import weakref
import json
from loguru import logger as log
import logging
logging.getLogger('trio-websocket').setLevel(logging.INFO)

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
        self._child_obj = weakref.WeakValueDictionary()
        self._subscr = defaultdict(list, {})

        self._watched_children = weakref.WeakValueDictionary()
        self._watch_poll_delay = 0.2
        self._children_updates = defaultdict(dict, {})

        self._cancel_scope = trio.CancelScope()
        self._running = True

        self._register_child(self.vars)

    def serialize_value(self, value):
        return str(value)

    def watch_obj(self, obj):
        self._watched_children[ref(obj)] = obj
        self._child_obj[ref(obj)] = obj

    def _register_new(self, name, value):
        """ Make `Object` children of this Object also be listened """
        obj_map(value, self._register_child)

    def _register_child(self, o):
        if isinstance(o, Object):

            def put_updates(name, value):
                """ Put the updates to temp dictionary """
                name, value = o._prepare_send(name, value)
                # Determines what to send to ws clients
                self._children_updates[ref(o)].update({name:value})

            o.subscribe_set(put_updates)
            o.subscribe_set(self._register_new)

            # Determines where to put received updates
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
            log.debug(f"Children objects refs: {list(self._child_obj.keys())}")
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
        # Subscribe this ws client to monitor vars
        # send the current object to it
        child = self._child_obj.get(ref)
        if child is None:
            log.error("No child with ref {}", ref)
            return

        self._subscr[ref].append( ws )

        # if updates to other clients sent, 
        # Initiate state for current cliet
        if not self._children_updates[ref]:
            x =  self._full_object_prepare(child)
            log.info("Yield initial update {}",x)
            yield x

        # ?B: submit listening coro of this particular object to nursery
        await self._child_updating_loop(ws, child)
        yield None

    def _full_object_prepare(self, obj):
        if isinstance(obj, Object):
            x = {}
            for name, value in obj.items():
                name, value = obj._prepare_send(name, value)
                x[name] = value
            x = json.dumps(x)
            return x
        else:
            return self.serialize_value(obj)


    async def _child_updating_loop(self, ws, child):
        """ Listen for incomming updates from websocket
        and update the relevant child

        This coroutine works N times, where N is number of
        requested existing objects (from `self._child_obj`)
        """
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

    # ?A: Constantly serve all objects updates
    async def _poll_objects(self):
        while True:
            for ref_ in self._watched_children:
                message = self._full_object_prepare(self._watched_children[ref_])
                log.debug(f"Poller sending updates to {ref_}")
                await self._send_message_to_subscribers(ref_, message)
            await trio.sleep(self._watch_poll_delay)

    async def _monitor_updates(self):
        while True:
            for ref_ in self._children_updates:
                # __setattr__ hooks will put updates here
                updates = self._children_updates[ref_]
                if updates:
                    message = json.dumps(updates)
                    await self._send_message_to_subscribers(ref_, message)
                    self._children_updates[ref_] = {}
            await trio.sleep(.02)

    async def _send_message_to_subscribers(self, ref_, message):
        """Get subscribers of ref and send them updates"""
        subscribers = self._get_alive_subscribers(ref_)
        self._subscr[ref_] = subscribers
        if not len(subscribers):
            return
        for ws in subscribers:
            try:
                await ws.send_message(message)
            except Exception as e:
                log.error("Error sending update to {}: {}", ws, e)


    def _get_alive_subscribers(self, ref):
        subscribers  = self._subscr[ref]
        return [ ws for ws in subscribers if not ws.closed]

## ## ## ## ## ## Starting ## ## ## ## ## ## 

    async def _start(self):
        args = (self.addr, self.port, self._handler)
        try:
            async with trio.open_nursery() as nursery:
                self._cancel_scope = nursery.cancel_scope
                nursery.start_soon(self._watch_for_cancel)
                nursery.start_soon(start_server, *args+(nursery,))
                nursery.start_soon(self._monitor_updates)
                nursery.start_soon(self._poll_objects)
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
