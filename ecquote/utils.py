#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import functools
import itertools
import re
from contextlib import contextmanager


def progress(x):
    try:
        from tqdm import tqdm
    except ImportError:
        return x

    if len(x) > 10000:
        return tqdm(x)

    return x


def cached_method(method):
    name = f"_{method.__name__}"

    @functools.wraps(method)
    def wrapped(self):
        if getattr(self, name, None) is None:
            setattr(self, name, method(self))
        return getattr(self, name)

    return wrapped


CACHED = {}


def cached_function(func):
    name = (func.__name__, func.__hash__())

    @functools.wraps(func)
    def wrapped(*args):
        key = (name, args)
        if key not in CACHED:
            CACHED[key] = func(*args)
        return CACHED[key]

    return wrapped


ONCE = set()
REQUEST = []


@contextmanager
def capture_warnings(request):
    global REQUEST
    REQUEST.append(request)
    try:
        yield request
    finally:
        REQUEST.pop()


def log_warning_once(
    logger,
    fmt,
    *args,
    raise_exception=False,
    raise_if_strict_mode=False,
):
    from .resources import config

    if raise_if_strict_mode and config("strict-mode"):
        raise_exception = ValueError

    msg = fmt % args
    if raise_exception:
        raise raise_exception(msg)
    if REQUEST:
        REQUEST[-1].add_warning(re.sub(r"\s*\(.*?\)$", "", msg))
    # else:
    #     raise ValueError(f"No request associated with warning {msg}")

    if msg not in ONCE:
        logger.warning("%s", msg)
        ONCE.add(msg)


def as_dict(x):

    if hasattr(x, "as_dict"):
        return as_dict(x.as_dict())

    if isinstance(x, (list, tuple, set)):
        return [as_dict(y) for y in x]

    if isinstance(x, dict):
        return {k: as_dict(v) for k, v in x.items()}

    return x


def as_numbers(x):

    if isinstance(x, (list, tuple)):
        return [as_numbers(y) for y in x]

    if isinstance(x, dict):
        return {k: as_numbers(v) for k, v in x.items()}

    try:
        return int(x)
    except ValueError:
        pass

    try:
        return float(x)
    except ValueError:
        pass

    return x


def as_resource(x):
    if isinstance(x, str):
        if x.lower() in ["true", "yes", "on"]:
            return True
        if x.lower() in ["false", "no", "off"]:
            return False
    return as_numbers(x)


def as_string(x):

    if x is None:
        return x

    if isinstance(x, (list, tuple)):
        return [as_string(y) for y in x]

    if isinstance(x, dict):
        return {k: as_string(v) for k, v in x.items()}

    return str(x)


def bytes(n):
    u = ["", " KiB", " MiB", " GiB", " TiB", " PiB", "EiB", "ZiB", "YiB"]
    i = 0
    while n >= 1024:
        n /= 1024.0
        i += 1
    return "%g%s" % (int(n * 10 + 0.5) / 10.0, u[i])


ROMAN = dict(i=1, ii=2, iii=3, iv=4, v=5, vi=6, vii=7, viii=8, ix=9, x=10)


def roman(s):
    return tuple(
        ROMAN.get(x, x) if i < 2 else x for i, x in enumerate(s.lower().split("-"))
    )


def iterate_request(r):
    s = {}
    for k, v in r.items():
        if not isinstance(v, (tuple, list)):
            s[k] = [v]
        else:
            s[k] = v
    yield from (dict(zip(s.keys(), x)) for x in itertools.product(*s.values()))


def plural(n, what):
    if n == 1:
        return f"{n} {what}"
    if what.endswith("y"):
        return plural(n, what[:-1] + "ie")
    return f"{n} {what}s"
