import threading
import weakref
from legimens import ref
from legimens import async_sleep
from loguru import logger as log


class Watcher:
    def __init__(self, leapp, delay=0.5):
        """
        Allows to periodically send updates of a mutable object.
        Re-triggers updates in Legimens object by calling __setattr__
        every `delay` seconds.

        Effectively, this is a handy wrapper to do this:

            while True:
                obj.__setattr__(attr, value) # sends updates
                sleep(delay)

        Args:
            leapp (legimens.App): instance of legimens app
            delay (float): delay between updates in seconds
        """
        self.leapp = leapp
        self._watched_obj = weakref.WeakValueDictionary()
        self._delay = delay
        self._lock = threading.RLock()

        leapp.schedule_coroutine(self.main_coro)

    def set_delay(self, delay):
        """ Set delay between updates (re-assigninments). """
        self._delay = delay

    @staticmethod
    def watched_obj_key(obj, attr):
        return ref(obj), attr

    @staticmethod
    def _assign_update(obj, attr, value):
        log.debug("watcher sets {}.{} to {}", ref(obj), attr, value)
        try:
            # This will make an update assignment to legimens:
            # legimens.App._children_updates[ref(obj)] = {attr: value}
            obj.__setattr__(attr, value)
        except Exception as e:
            log.error("Failed to to assign attribute {}: {}", attr, e)


    def bind(self, obj, attr, value):
        """
        Start assigning `value` to `obj`.`attr` every `delay` seconds
        Args:
            obj (legimens.Object): object that will send updates
            attr (str): attribute of `obj`
            value: mutable object
        """
        _key = self.watched_obj_key(obj, attr)
        with self._lock:
            self._watched_obj[_key] = obj
        self._assign_update(obj, attr, value)
        log.debug("keys that watched {}", list(self._watched_obj.keys()))


    def unbind(self, obj, attr):
        """ Stop watching value that was bound to `obj`.`attr`. """
        _key = self.watched_obj_key(obj, attr)
        with self._lock:
            del self._watched_obj[_key]

    def clear(self):
        """ Stop watching anything in this watcher. """
        with self._lock:
            self._watched_obj.clear()

    async def main_coro(self):
        while True:
            #log.trace("Watcher loop step; watched: {}", list(self._watched_obj.keys()))
            with self._lock:
                for key in self._watched_obj:
                    obj = self._watched_obj[key]
                    _, attr = key
                    value = obj.__getattr__(attr)
                    self._assign_update(obj, attr, value)
            await async_sleep(self._delay)
