def obj_map(d, pre):
    x = pre(d)
    if x is not None: return x

    if isinstance(d, list):
        return [obj_map(x, pre) for x in d]
    if isinstance(d, dict):
        d_ = {}
        for k in d:
            d_[k] = obj_map(d[k], pre)
        return d_
    return d

def inplace_obj_map(d, pre):
    raise NotImplementedError
