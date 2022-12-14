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

LOG = logging.getLogger(__name__)


def list_of_tests():
    top = os.path.join(os.path.dirname(__file__), "representations")
    tests = {}
    for root, _, files in os.walk(top):
        for file in files:
            if file.endswith(".req"):
                full = os.path.join(root, file)
                key = full[len(top) + 1 : -4]
                tests[key] = full

    return tests


TESTS = list_of_tests()
TESTS = []


@pytest.mark.parametrize("req", TESTS)
def test_representation(req):
    path = TESTS[req]

    cart = Cart.from_request_files(path, inherit=False)
    cart.costing()  # This will trigger a lookup of data represenation


if __name__ == "__main__":
    print(list_of_tests())
