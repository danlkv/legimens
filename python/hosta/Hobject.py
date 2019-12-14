from hosta.helpers.AttrDict import AttrSubscrDict
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
        for k in self:
            if isinstance(self[k], Hobject):
                children.append(self[k])
        return children

    def serial(self):

        x = json.dumps({k:str(v) for k,v in self.items()})
        return x
