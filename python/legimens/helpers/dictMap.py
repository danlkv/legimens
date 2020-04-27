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

def keys_recursive_map(d, post):
    if isinstance(d, list):
        return [obj_map(x, post) for x in d]
    if isinstance(d, dict):
        d_ = {}
        for k in d:
            d_[k] = obj_map(d[k], post)
        return d_
    return post(d)

