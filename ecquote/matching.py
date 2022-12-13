#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging
from collections import defaultdict

from .resources import resource
from .utils import iterate_request, log_warning_once

LOG = logging.getLogger(__name__)


def to_by(values):

    start = int(values[0])
    end = int(values[2])
    step = int(values[4])
    assert start < end
    assert step > 0
    values = []
    for n in range(start, end + step, step):
        values.append(str(n))

    return [str(x) for x in values]


def multiple(name, request, matches, callable):
    from .request import Request

    SOME = ("param", "step")
    if request.number_of_fields() != sum(r.number_of_fields() for r, _ in matches):
        LOG.error(
            "%s: request matches many sets: %s %s != %s",
            name,
            request.number_of_fields(),
            request,
            sum(x.number_of_fields() for x, _ in matches),
        )
        for r, s in matches:
            LOG.error("%s: %s %s %s", name, s, r.number_of_fields(), r)

        allfields = set()
        some = {k: v for k, v in request.fields.items() if k in SOME}
        for one in iterate_request(some):
            f = tuple(sorted(one.items()))
            allfields.add(f)

        seen = {}

        for r, s in matches:
            some = {k: v for k, v in r.fields.items() if k in SOME}
            for one in iterate_request(some):

                f = tuple(sorted(one.items()))
                allfields.discard(f)

                if f in seen:
                    LOG.error("Duplicated field in %s and %s: %s", s, seen[f], f)
                else:
                    seen[f] = s

        if allfields:
            for a in allfields:
                c = Request({k: (v,) for k, v in a})
                LOG.error("Fields not covered: %s", c)

        raise ValueError(
            "Request matches many %s %s %s" % (name, [s for _, s in matches], request)
        )
    return callable(matches)


class Matcher:
    def __init__(
        self,
        what,
        callable,
        *,
        multiple=None,
        default=None,
        error=None,
        issue_warning=True,
    ):
        self.what = what

        self._rules = None
        self._cache = {}
        self._default = default
        self.seen = set()
        self.callable = callable
        self._keys = None
        self.issue_warning = issue_warning
        self.multiple = multiple
        self.error = error

    @property
    def rules(self):
        if self._rules is None:

            if isinstance(self.what, str):
                self._rules = resource(self.what)
            else:
                self._rules = self.what
                self.what = "<given>"

            if isinstance(self.rules, list):
                self._rules = {k: v for k, v in enumerate(self._rules)}

            for rule in self._rules.values():
                mars = rule["mars"]
                for k, v in mars.items():
                    if isinstance(v, (list, tuple)):
                        if len(v) == 5 and v[1] == "to" and v[3] == "by":
                            mars[k] = to_by(v)

        return self._rules

    def get_match(self, request):
        if self._keys is None:
            # First time
            return self._get_match(request)

        key = tuple(request.fields.get(k) for k in self._keys)
        if key not in self._cache:
            return self._get_match(request)

        # print("MATCH", key, self._cache[key],self._keys)
        return self._cache[key]

    def _get_match(self, request):
        from .request import Request

        matches = []
        keys = set()
        best = defaultdict(list)

        for i, (name, s) in enumerate(self.rules.items()):
            s["order"] = i
            if s.get("default", False):
                self._default = name
                self.issue_warning = s.get("warning", True)
                continue
            mars = s["mars"]
            cnt = 0

            for k, v in mars.items():
                keys.add(k)

                if not isinstance(v, list):
                    v = [v]

                v = set(str(x) if x is not None else None for x in v)

                if k in request.fields:
                    if set(request.fields[k]).intersection(v):
                        cnt += 1
                else:
                    if None in v:
                        cnt += 1

            best[cnt].append(name)

            if cnt == len(mars):
                matches.append(name)

        self._keys = sorted(keys)

        if len(matches) == 0:

            if callable(self._default):
                return self._default(request)

            if self.error:
                self.error(request)

            if self.issue_warning:
                r = {k: request.fields[k] for k in keys if k in request.fields}
                # r = str(Request(r, target=(request.target,)))
                r = str(Request(r))
                if r not in self.seen:

                    if self._default is None:
                        LOG.error(
                            "No %s found for %s. %r.",
                            self.what.replace("_", " "),
                            r,
                            request,
                        )
                        b = max(best.keys())
                        LOG.error("Best matches: %s", best[b])

                    log_warning_once(
                        LOG,
                        "No %s found for %s, %s. %r.",
                        self.what.replace("_", " "),
                        r,
                        "using default" if self._default else "no default provided",
                        request,
                        raise_exception=ValueError if self._default is None else False,
                    )
                    self.seen.add(r)
            assert self._default is not None
            matches = [self._default]

        if len(matches) > 1:
            name = self.what.replace("_", " ")

            if self.multiple:
                return multiple(
                    name, request, self.split_request(request, matches), self.multiple
                )

            r = {k: request.fields[k] for k in keys if k in request.fields}
            sets = [m for m in matches]

            raise ValueError(f"Request matches several {name}: {sets} {r} ({request}).")

        key = tuple(request.fields.get(k) for k in self._keys)
        name = matches[0]
        try:
            kwargs = dict(**self.rules[name])
            LOG.debug("Matching %s: %s %s (%s)", self.what, name, kwargs, request)
            kwargs.pop("default", None)
            self._cache[key] = self.callable(name, **kwargs)
            return self._cache[key]
        except TypeError as e:
            LOG.error("%s: %s", name, e)
            raise

    def split_request(self, request, matches):
        result = []
        for m in matches:
            result.append(self.split_one(request, m))
        return result

    def split_one(self, request, name):
        from .request import Request

        rule = self.rules[name]
        mars = rule["mars"]
        split = {}
        for k, v in mars.items():

            if not isinstance(v, list):
                v = [v]
            v = set([str(x) if x is not None else x for x in v])
            assert None not in v, v
            if k in self._keys:
                split[k] = tuple(
                    [x for x in request.fields[k] if x in v]
                )  # Preserve order
                assert split[k], (k, v)
        return Request(request, split), self.callable(name, **dict(**rule))
