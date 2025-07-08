#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from ecquote.costing import band as yearly_band


def band(x):
    return yearly_band(x * 365 * 1024 * 1024 * 1024)[1]


def test_band():
    assert band(0) == 0
    assert band(1) == 0
    assert band(2) == 1000
    assert band(10) == 1000
    assert band(11) == 7000
    assert band(50) == 7000
    assert band(51) == 7000
    assert band(100) == 7000
    assert band(101) == 33000
    assert band(500) == 33000
    assert band(501) == 60000
    assert band(1000) == 60000
    assert band(1001) == 90000
    assert band(4000) == 90000
    assert band(4001) == 180000
    assert band(8000) == 180000
    assert band(8001) is None


if __name__ == "__main__":
    test_band()
