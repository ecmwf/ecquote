#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging
import os

import pytest

from ecquote.cart import Cart
from ecquote.utils import as_numbers

LOG = logging.getLogger(__name__)


def list_of_tests():
    top = os.path.join(os.path.dirname(__file__), "reference")
    tests = {}
    for root, _, files in os.walk(top):
        for file in files:
            if file.endswith(".req"):
                full = os.path.join(root, file)
                key = full[len(top) + 1 : -4]
                tests[key] = full

    return tests


TESTS = list_of_tests()

percent = 0.0


@pytest.mark.parametrize("req", TESTS)
def test_references(req):
    path = TESTS[req]

    cost = {}
    with open(path) as f:
        for line in f:
            if line.startswith("# "):
                if "=" in line:
                    key, value = line[2:].strip().split("=")
                    cost[key.strip()] = as_numbers(value.strip())

    cart = Cart.from_request_files(path, inherit=True)
    costing = cart.costing()
    ok = False

    if "epus" in cost:
        ok = True
        epus = costing["total"]["epus"]

        assert epus == cost["epus"]

    if "subset" in cost:
        ok = True
        for r in cart.requests:
            if not r.subset.name.startswith("X-"):
                assert r.subset.name.replace("-cf", "") == cost["subset"]

    if "group" in cost:
        ok = True
        for r in cart.requests:
            assert r.group == cost["group"]

    if not ok:
        raise ValueError("Nothing to check")
