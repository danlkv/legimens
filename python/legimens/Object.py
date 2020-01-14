from legimens.helpers.AttrDict import AttrSubscrDict
from legimens.helpers.dictMap import obj_map

import json

def ref(o):
    return f"Legi_{hex(id(o))}"

class Object(AttrSubscrDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _before_send(self, name, value):
        return name, value

    def _after_update(self, name, value):
        self[name] = value

    def _get_child_obj(self):
        children = []
        def _app(o):
            if isinstance(o, Object):
                children.append(o)
        for k in self:
            obj_map(self[k], pre=_app)
        return children

def serial(obj):
    def _tostr(o):
        if isinstance(o, Object):
            return ref(o)

    x = obj_map(obj, _tostr)
    x = json.dumps(x)
    return x

