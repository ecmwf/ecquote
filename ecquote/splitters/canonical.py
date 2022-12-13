#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging

from ..utils import log_warning_once

LOG = logging.getLogger(__name__)

TO_BY = {
    "number": 1,
    "levelist": 1,
    "fcmonth": 1,
    "direction": 1,
    "frequency": 1,
    "step": None,
}


def to_by(name, values):
    if len(values) == 3 and values[1].lower() == "to":
        start = int(values[0])
        end = int(values[2])
        if TO_BY[name] is None:
            raise ValueError(f"to/by not supported for '{name}', {values}")
        step = TO_BY[name]
        assert start < end
        assert step > 0
        values = []
        for n in range(start, end + step, step):
            values.append(str(n))

    if len(values) == 5 and values[1].lower() == "to" and values[3].lower() == "by":
        start = int(values[0])
        end = int(values[2])
        step = int(values[4])
        assert start < end
        assert step > 0
        values = []
        for n in range(start, end + step, step):
            values.append(str(n))

    return tuple(values)


def canonical_area(area):
    area = [float(x) for x in area]
    if len(area) == 4:
        n, w, s, e = area
        while e < w:
            e += 360
        area = n, w, s, e
    return tuple(str(x) for x in area)


def canonical_time(time):
    time = [int(x) for x in time]
    return tuple("%02d00" % (x / 100 if x > 100 else x) for x in time)


def canonical_grid(grid):
    if len(grid) == 2:
        try:
            return tuple(str(float(x)) for x in grid)
        except ValueError:
            pass
    return grid


def canonical_param(param):
    bad = None
    for p in param:
        try:
            float(p)
            bad = p
        except ValueError:
            pass

    if bad:
        raise ValueError(f"Parameters must not be numbers (param={bad})")

    return tuple(x.lower() for x in param)


def splitter(requests):
    # Cleanup requests
    for r in requests:

        r.fields.setdefault("class", ("od",))
        r.fields.setdefault("domain", ("g",))
        r.fields.setdefault("expver", ("0001",))

        for s in TO_BY.keys():
            if s in r.fields:
                r.fields[s] = to_by(s, r.fields[s])

        if "area" in r.postproc:
            r.postproc["area"] = canonical_area(r.postproc["area"])

        if "grid" in r.postproc:
            r.postproc["grid"] = canonical_grid(r.postproc["grid"])

        if "time" in r.fields:
            r.fields["time"] = canonical_time(r.fields["time"])

        if "param" in r.fields:
            r.fields["param"] = canonical_param(r.fields["param"])

        if "use" in r.use:
            r.use["use"] = tuple(u.lower() for u in r.use["use"])

        for g, s in r._groups.items():
            for k, v in s.items():
                assert isinstance(v, tuple), (g, k, v)
                for x in v:
                    assert isinstance(x, str), (g, k, x)

        for k, v in r.fields.items():
            assert len(set(v)) == len(v), (k, v)

        # Some sanity checks
        off = ("off",)

        if r.type == "pf":
            if r.fields.get("number", off) == off:
                log_warning_once(
                    LOG,
                    "Missing 'number' for type 'pf'. (%s)",
                    r,
                    raise_if_strict_mode=True,
                )

        yield r
