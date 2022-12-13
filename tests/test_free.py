#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from ecquote.cart import Cart
from ecquote.resources import resource_path


def test_gts():
    cart = Cart.from_request_files(
        resource_path("free-wmo-essential"),
        inherit=True,
    )

    c = cart.costing()
    assert c["total"]["epus"] == 0, c


def test_open_data():
    cart = Cart.from_request_files(
        resource_path("free-open-data"),
        inherit=True,
    )

    c = cart.costing()
    assert c["total"]["epus"] == 0, c


if __name__ == "__main__":
    test_gts()
