#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging

from .free_sets import match

LOG = logging.getLogger(__name__)


def splitter(requests, free_grid):
    if isinstance(free_grid, float):
        free_grid = [free_grid]

    if isinstance(free_grid, str):
        free_grid = tuple(float(x) for x in free_grid.split("/"))

    if len(free_grid) == 1:
        free_grid = (free_grid[0], free_grid[0])

    for r in requests:
        if match(r, free_grid):
            yield r.annotate("free", "free-grid", override="append")
            continue

        yield r
