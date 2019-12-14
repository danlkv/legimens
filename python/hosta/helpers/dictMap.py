def obj_map(d, pre, post=lambda x: x):
    x = pre(d)
    if x is not None: return x

    if isinstance(d, list):
        return [obj_map(x, pre, post) for x in d]
    if isinstance(d, dict):
        d_ = {}
        for k in d:
            d_[k] = obj_map(d[k], pre, post)
        return d_
    return post(d)

def inplace_obj_map(d, pre, post):
    raise NotImplementedError
