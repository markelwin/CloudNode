import builtins

def dictionary_parser(data_dict, dotted_keys_to_traverse, not_found_value=None):
    """Helpful function to retrieve one nested dictionary value using specific path. See iterative_dictionary_parser."""
    # NOTE: data=dict(a=1,c=dict(d=3, e=[4, 'giraffe'])) parsed by "c.e" would be return [4, 'giraffe']
    # NOTE: also can be used for conventional .get with default: i.e., parsed by "a" simply returns 1
    # NOTE: adding new features: a.0.b:int will now access lists and performs cast as well, i.e., int(dct["a"][0]["b"])
    # NOTE: dotted keys may now have '~' to represent when the key itself has a dot: a*b.c is dct["a.b"]["c"]
    # NOTE: lastly the token [*] means to iterate over the entire list: a.[*].b returns a list of all key b of list a
    dotted_keys_to_traverse, cast = dotted_keys_to_traverse.split(":") if ":" in dotted_keys_to_traverse else (dotted_keys_to_traverse, None)
    keys_to_traverse = dotted_keys_to_traverse.split(".")
    keys_to_traverse = ["[*]" if key == "[*]" else key.replace("*", ".") for key in keys_to_traverse]
    tree = data_dict
    for key_i, key in enumerate(keys_to_traverse):
        # to handle if key is the list glob [*]
        if key == "[*]":
            _remaining_dotted_keys = ".".join([k.replace(".", "*") for k in keys_to_traverse[key_i+1:]])
            return [dictionary_parser(d, _remaining_dotted_keys, not_found_value=not_found_value) for d in tree]
        # to handle if tree is a list:
        if isinstance(tree, (list, tuple)) and len(tree) > int(key):
            tree = tree[int(key)]
            if cast is not None and key_i == len(keys_to_traverse) - 1: tree = getattr(builtins, cast)(tree)
        elif isinstance(tree, dict) and key in tree:
            tree = tree[key]
            if cast is not None and key_i == len(keys_to_traverse) - 1: tree = getattr(builtins, cast)(tree)
        else:
            tree = not_found_value
            break
    return tree


def dictionary_keep_these_keys(data_dict, keys_to_keep, not_found_value=None):
    """Helpful function for paring a dictionary to only selected keys; replacing missing keys with not_found_value"""
    how_to_parse = {k:k for k in keys_to_keep}
    return iterative_dictionary_parser(data_dict, how_to_parse, not_found_value=not_found_value)


def iterative_dictionary_parser(data_dict, how_to_parse, not_found_value=None):
    """Helpful function for traversing dictionary and extracting only specific branches and key-values."""
    # NOTE: data=dict(a=1, b=2, c=dict(d=3, e=[4, 'giraffe'])) parsed by parse=dict(out1="a", out2="c.e", out3="c.f")
    # would result in the dictionary retval=dict(out1=1, out2=[4, 'giraffe'], out3=None) for any value datatypes.
    return {name: dictionary_parser(data_dict, how_to, not_found_value=not_found_value) for name, how_to in how_to_parse.items()}


def iterative_dictionary_parser_as_list(data_dict, how_to_parse, not_found_value=None):
    """Helpful function for traversing dictionary and extracting only specific branches and key-values, list input."""
    # NOTE: Same as iterative_dictionary_parser except the input how_to_parse and outputs are a list, not a dictionary.
    return [dictionary_parser(data_dict, how_to, not_found_value=not_found_value) for how_to in how_to_parse]


def alphabetical_dict_by_keys_nested(dct):
    return {k: alphabetical_dict_by_keys_nested(v) if isinstance(v, dict) else v for k, v in sorted(dct.items())}

