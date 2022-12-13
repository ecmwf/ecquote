#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

from .resources import config
from .utils import cached_function

LOG = logging.getLogger(__name__)


@cached_function
def land_sea_ratio_mask_reduced(north, west, south, east):
    from .landsea_mask_reduced import land_sea_ratio as ratio

    return ratio(north, west, south, east)


@cached_function
def land_sea_ratio_mask_regular(north, west, south, east):
    from .landsea_mask_regular import land_sea_ratio as ratio

    return ratio(north, west, south, east)


@cached_function
def land_sea_ratio_fixed(north, west, south, east):
    from .landsea_fixed import land_sea_ratio as ratio

    return ratio(north, west, south, east)


def land_sea_ratio(north, west, south, east, method=None):
    while east <= west:
        east += 360
    if method is None:
        method = config("landsea_ratio_method")
    result = dict(
        fixed=land_sea_ratio_fixed,
        mask=land_sea_ratio_mask_reduced,
        mask_reduced=land_sea_ratio_mask_reduced,
        mask_regular=land_sea_ratio_mask_regular,
    )[method](north, west, south, east)

    LOG.debug(
        "landsea ratio %s %s/%s/%s/%s %s", result, north, west, south, east, method
    )
    return result
