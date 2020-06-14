
class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self,  name, value):
        self[name] = value

class AttrCbDict(AttrDict):
    def __getattr__(self, name):
        #object.__getattribute__(self, '__get')(name)
        self._get(name)
        return super().__getattr__(name)

    def __setattr__(self, name, value):
        #object.__getattribute__(self, '__set')(name)
        """
        Two options:
            1. First call the callbacks, then set value
            2. Set value then call the callbacks

        1. Will not update the object until the callbacks called.
            This allows to modify mutable data before assignment

        2. Allows to treat the new object as updated in the callbacks.

        At start, this was 1. Then I changed it to 2 to fix
        the bug with setting new value -
        set callback was set to sending updates, that were not in object yet
        then changed to 1 back
        and then back to 2

        """

        super().__setattr__(name, value)
        self._set(name, value)

class AttrSubscrDict(AttrCbDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, '_set_subscribers', [])
        object.__setattr__(self, '_get_subscribers', [])


    def subscribe_get(self, subs):
        self._get_subscribers.append(subs)

    def subscribe_set(self, subs):
        self._set_subscribers.append(subs)


    def _get(self, name):
        [x(name) for x in object.__getattribute__(self,'_get_subscribers')]

    def _set(self, name, value):
        [x(name, value) for x in object.__getattribute__(self,'_set_subscribers')]
