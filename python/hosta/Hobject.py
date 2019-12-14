from hosta.helpers.AttrDict import AttrSubscrDict
from hosta.helpers.dictMap import obj_map

import json

class Hobject(AttrSubscrDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, '_touched', True)

    def _set(self, name, value):
        super()._set(name, value)
        object.__setattr__(self, '_touched', True)

    def __repr__(self):
        return f"Hobj_{hex(id(self))}"

    def _mark_untouched(self):
        object.__setattr__(self, '_touched', False)

    def _get_child_obj(self):
        children = []
        def _app(o):
            if isinstance(o, Hobject):
                children.append(o)
        for k in self:
            obj_map(self[k], pre=_app, post=lambda x: x)
        return children

    def serial(self):
        def _tostr(o):
            if o == self: return
            if isinstance(o, Hobject):
                return repr(o)

        x = obj_map(self, _tostr)
        x = json.dumps(x)
        return x

