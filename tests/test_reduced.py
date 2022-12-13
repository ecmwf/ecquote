#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

import pytest

from ecquote.grid import full_reduced_grid

LOG = logging.getLogger(__name__)


GRIDS = {
    "F1280": 13107200,
    "F160": 204800,
    "F200": 320000,
    "F256": 524288,
    "F320": 819200,
    "F400": 1280000,
    "F640": 3276800,
    "N128": 88838,
    "N160": 138346,
    "N200": 213988,
    "N256": 348528,
    "N320": 542080,
    "N400": 843490,
    "N640": 2140702,
    "N80": 35718,
    "O1280": 6599680,
    "O320": 421120,
    "O640": 1661440,
    "N1280": 8505906,
    "reduced-0_125": 2640892,
    "reduced-0_25": 660428,
    "reduced-0_5": 165184,
}


@pytest.mark.parametrize("grid", GRIDS.keys())
def test_reduced(grid):
    assert full_reduced_grid(grid) == GRIDS[grid]
