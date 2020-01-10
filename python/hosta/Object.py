from legimens.helpers.AttrDict import AttrSubscrDict
from legimens.helpers.dictMap import obj_map

import json

def ref(o):
    return f"Legi_{hex(id(o))}"

class Object(AttrSubscrDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._touch()

    def _set(self, name, value):
        super()._set(name, value)
        self._touch()

    def _touch(self):
        object.__setattr__(self, '_touched', True)

    def _mark_untouched(self):
        object.__setattr__(self, '_touched', False)

    def _get_child_obj(self):
        children = []
        def _app(o):
            if isinstance(o, Object):
                children.append(o)
        for k in self:
            obj_map(self[k], pre=_app)
        return children

    def ref(self):
        return ref(self)

    def serial(self):
        def _tostr(o):
            if o is self: return
            if isinstance(o, Object):
                return ref(o)

        x = obj_map(self, _tostr)
        x = json.dumps(x)
        return x

