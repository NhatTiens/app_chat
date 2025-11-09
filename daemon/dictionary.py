# Case-insensitive dict compatible with the original API.
try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping


class CaseInsensitiveDict(MutableMapping):
    """
    Dict-like container with case-insensitive keys.
    """

    def __init__(self, *args, **kwargs):
        self._store = {}
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self._store[key.lower()]

    def __setitem__(self, key, value):
        self._store[key.lower()] = value

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __repr__(self):
        return repr(self._store)
