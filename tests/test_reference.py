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


def key_to_issue(key):
    return f"issues/reference-{key}.req"


def list_of_tests():
    top = os.path.join(os.path.dirname(__file__), "reference")
    tests = {}
    for root, _, files in os.walk(top):
        for file in files:
            if file.endswith(".req"):
                full = os.path.join(root, file)
                key = full[len(top) + 1 : -4]
                tests[key] = full

    if False:
        tst = {}
        for t in tests.keys():
            issue = key_to_issue(t)
            if os.path.exists(issue):
                tst[t] = tests[t]

        if tst:
            return tst

    return tests


TESTS = list_of_tests()

percent = 0.0


@pytest.mark.parametrize("req", TESTS)
def test_references(req):
    path = TESTS[req]

    issue = key_to_issue(req)
    cart = None

    cost = {}
    with open(path) as f:
        for line in f:
            if line.startswith("# "):
                if "=" in line:
                    key, value = line[2:].strip().split("=")
                    key = key.strip()
                    value = value.strip()
                    if "," in value:
                        cost[key] = value.split(",")
                    else:
                        cost[key] = as_numbers(value)

    if "skip" in cost:
        raise pytest.skip(cost["skip"])

    try:
        assert len(cost) <= 3

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
                    subset = r.subset.name.replace("-cf", "")
                    assert (subset == cost["subset"]) or (isinstance(cost["subset"], list) and subset in cost["subset"])

        if "group" in cost:
            ok = True
            for r in cart.requests:
                assert r.group == cost["group"]

        if not ok:
            raise ValueError("Nothing to check")

    except Exception:
        if cart is None:
            cart = Cart.from_request_files(path, inherit=True)
        path = os.path.dirname(issue)
        if not os.path.exists(path):
            os.mkdir(path)
        with open(issue, "w") as f:
            for k, v in sorted(cost.items()):
                print(f"# {k}={v}", file=f)
            print(file=f)
            cart.dump_requests(file=f)
        raise
