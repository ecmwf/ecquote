#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging

import yaml

from .request import Request

LOG = logging.getLogger(__name__)


class CompareLLGrid:
    def __init__(self, v):
        self.v = tuple(float(x) for x in v)

    def same(self, value):
        try:
            return self.v == tuple(float(x) for x in value)
        except ValueError:
            pass

        return False

    def value(self):
        return tuple(str(x) for x in self.v)


class DefaultCompare:
    def __init__(self, v):
        if isinstance(v, list):
            self.v = tuple(v)
        else:
            self.v = (v,)

    def same(self, value):
        return self.v == value

    def __repr__(self):
        return repr(self.v)


def compare_grid(v):
    v = v.split("/")
    if len(v) == 2:
        return CompareLLGrid(v)

    if len(v) == 1:
        v = v[0]
        assert v[0] in ("O", "N"), v
        return DefaultCompare(v)

    raise NotImplementedError(v)


def tidy(d):
    compare = dict(grid=compare_grid)
    for k, v in list(d.items()):
        d[k] = compare.get(k, DefaultCompare)(v)


class Rule:
    def __init__(self, rule):
        self.condition, self.action = rule
        tidy(self.condition)
        tidy(self.action)

        # LOG.debug("rule: %s", self.condition)
        # LOG.debug("   -: %s", self.action)

    def match(self, r):
        for k, v in self.condition.items():
            if not v.same(r.get(k)):
                return False
        return True

    def apply(self, r):
        r = dict(**r)
        for k, v in self.action.items():
            r[k] = v.value()
        return r


class Modifier:
    def __init__(self, path):
        with open(path) as f:
            self.rules = [Rule(r) for r in yaml.safe_load(f)]

    def __call__(self, r):

        save = r

        for rule in self.rules:
            if rule.match(r):
                r = rule.apply(r)

        if save is not r:
            print("Changing:", Request(save))
            print("      To:", Request(r))
            print()

        return r


def preprocessor(path):
    if path is None:
        return None
    else:
        return Modifier(path)
