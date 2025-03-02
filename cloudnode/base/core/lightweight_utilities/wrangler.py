import builtins


def dictionary_traverser(data, dotted_keys, not_found=None):
    """Retrieves one nested dictionary value described by dotted_keys. See dictionary_wrangler."""
    # NOTE: data=dict(a=1,c=dict(d=3, e=[4, 'giraffe'])) parsed by "c.e" would be return [4, 'giraffe']
    # NOTE: also can be used for conventional .get with default: i.e., parsed by "a" simply returns 1
    # NOTE: adding new features: a.0.b:int will now access lists and performs cast as well, i.e., int(dct["a"][0]["b"])
    # NOTE: dotted keys may now have '*' to represent when the key itself has a dot: a*b.c is dct["a.b"]["c"]
    # NOTE: lastly the token [*] means to iterate over the entire list: a.[*].b returns a list of all key b of list a
    dotted_keys, cast = dotted_keys.split(":") if ":" in dotted_keys else (dotted_keys, None)
    key_sequence = dotted_keys.split(".")

    tree = data
    for depth_i, key in enumerate(key_sequence):
        if key == "[*]":  # to handle if key is the list glob [*] construct list of explicit dotted_keys values
            _remaining_depths = ".".join(key_sequence[depth_i+1:])
            return [dictionary_traverser(d, _remaining_depths, not_found=not_found) for d in tree]

        key = key.replace("*", ".")  # to allow users to user * as . inside a key
        if isinstance(tree, (list, tuple)) and len(tree) > int(key):  # tree is a list; get its key-th item
            tree = tree[int(key)]
            if cast is not None and depth_i == len(key_sequence)-1: tree = getattr(builtins, cast)(tree)
        elif isinstance(tree, dict) and key in tree:
            tree = tree[key]
            if cast is not None and depth_i == len(key_sequence)-1: tree = getattr(builtins, cast)(tree)
        else:
            tree = not_found
            break
    return tree


def dictionary_wrangler(data, how_to_parse, not_found=None):
    """Helpful function for traversing dictionary and extracting only specific branches and key-values."""
    # NOTE: data=dict(a=1, b=2, c=dict(d=3, e=[4, 'giraffe'])) parsed by parse=dict(out1="a", out2="c.e", out3="c.f")
    # would result in the dictionary retval=dict(out1=1, out2=[4, 'giraffe'], out3=None) for any value datatypes.
    return {name: dictionary_traverser(data, how_to, not_found=not_found) for name, how_to in how_to_parse.items()}
