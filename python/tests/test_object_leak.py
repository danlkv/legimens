import gc
from legimens import Object, App


def test_leak_in_children():
    """
implicit watching funcitonality.

    Adding many (N) objects should not result in all them stored in _child_obj
    """
    app = App(addr='127.0.0.1', port=8082)

    class Int(Object):
        def __init__(self, value):
            super().__init__()
            self.value = value

    N = 100
    for i in range(N):
        print(id(i))
        app.vars.mamba = Int(i)

    assert len(list(app._child_obj.keys())) < N+1
    gc.collect()
    assert len(list(app._child_obj.keys())) == 2

def test_leak_in_children():
    """
integrated functionality

    Adding many (N) objects and getting updates should not reult in mayn keys in updates.
    """
    pass
