from enforce_typing import enforce_types


@enforce_types
def remove_dups(seq: list):
    """Returns all the items of seq, except duplicates. Preserves x's order."""

    # the implementation below is the fastest according to stackoverflow
    # https://stackoverflow.com/questions/480214/how-do-i-remove-duplicates-from-a-list-while-preserving-order
    seen = set()  # type: ignore[var-annotated]
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


@enforce_types   
def obj_in_objlist(obj, objlist: list) -> bool:
    """Return True if object 'obj' is in 'objlist'.
    Relies on the object's equality operator.
    """
    for obj_i in objlist:
        if obj == obj_i:
            return True
    return False
