#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

from .grid import reduced_grid_indices
from .resources import resource
from .utils import cached_function

LOG = logging.getLogger(__name__)


class Mask:
    def __init__(self, mask):

        state = mask["start"]
        size = mask["size"]
        grid = mask["grid"]

        LOG.debug("mask %s", (size, grid))

        indexes = mask["indexes"] + [size]
        values = [state] * size
        next_idx = 0

        for i in range(size):
            if i == indexes[next_idx]:
                state = not state
                next_idx += 1
            values[i] = state

        self.values = values
        self.name = mask["name"]
        self.size = size

        # with open("x.pgm", "w") as f:
        #     print("P1", file=f)
        #     w, h = mask["shape"]
        #     print(f"{w} {h}", file=f)
        #     for v in values:
        #         print(1 if v else 0, file=f)

        # cnt, size = self._land_sea_ratio(90, 0, -90, 360)
        # assert size == self.size, (size, self.size, size - self.size)

    def _land_sea_ratio(self, north, west, south, east):
        LOG.debug("Landsea %s/%s/%s/%s", north, west, south, east)
        idx = reduced_grid_indices(self.name, north, west, south, east)
        cnt = 0
        size = 0
        LOG.debug("Land-sea %s", (north - south) / 0.5)
        for start, end in idx:
            size += end - start + 1
            cnt += sum(self.values[start:end])
        return cnt, size

    def land_sea_ratio(self, north, west, south, east):
        cnt, size = self._land_sea_ratio(north, west, south, east)
        return cnt / size


MASK = None


@cached_function
def land_sea_ratio(north, west, south, east):
    global MASK
    if MASK is None:
        MASK = Mask(resource("wave-mask-regular"))
    return MASK.land_sea_ratio(north, west, south, east)
