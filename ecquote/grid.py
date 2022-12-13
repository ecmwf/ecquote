#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import json
import logging

from .resources import resource_path
from .utils import cached_function, log_warning_once

LOG = logging.getLogger(__name__)


def grid_rounding(x):
    if x < 0:
        return -grid_rounding(-x)
    return int(x * 1000000 + 0.5) / 1000000


epsilon = 1e-7


def less_or_equal(a, b):
    return a - epsilon <= b


@cached_function
def _latitudes_and_pls(name):
    path = resource_path(name)
    LOG.info("Loading latitudes/pls from %s" % path)
    with open(path) as f:
        data = json.load(f)
        return data["latitudes"], data["pl"]


@cached_function
def number_of_pl(name, north, south):
    latitudes, pl = _latitudes_and_pls(name)
    idx = [
        i
        for (i, lat) in enumerate(latitudes)
        if less_or_equal(lat, north) and less_or_equal(south, lat)
    ]
    return len(idx)


def _reduced_longitudes(name, north, west, south, east):
    assert west <= east, (west, east)
    assert west < 360
    assert east - west <= 360

    while east < 0:
        east += 360
        west += 360

    while east > 360:
        east -= 360
        west -= 360

    latitudes, pl = _latitudes_and_pls(name)

    idx = [
        i
        for (i, lat) in enumerate(latitudes)
        if less_or_equal(lat, north) and less_or_equal(south, lat)
    ]

    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug("North/south %s %s", latitudes[idx[0]], latitudes[idx[-1]])
        LOG.debug("IDX %s-%s (%s)", idx[0], idx[-1], len(idx))

    def condition_1(lon, west, east):
        return less_or_equal(lon, east) and less_or_equal(west, lon)

    def condition_2(lon, west, east):
        return less_or_equal(lon, east) or less_or_equal(west + 360, lon)

    if west >= 0 and east >= 0:
        condition = condition_1
    else:
        assert east >= 0
        condition = condition_2

    last = -1
    for i in idx:
        if pl[i] != last:
            we = 360 / pl[i]
            last = pl[i]
            lons = [360 * j / pl[i] for j in range(pl[i])]
            lons = sum(1 for lon in lons if condition(lon, west, east))

        yield i, lons, we, latitudes[i]


@cached_function
def _reduced_number_of_values(name, north, west, south, east):
    cnt = 0
    for _, lons, _, _ in _reduced_longitudes(name, north, west, south, east):
        cnt += lons

    LOG.debug(
        "_reduced_number_of_values %s %s %s %s %s %s",
        name,
        north,
        west,
        south,
        east,
        cnt,
    )
    return cnt


@cached_function
def _reduced_grid_indices(name, north, west, south, east):
    _, pl = _latitudes_and_pls(name)

    while east < 0:
        east += 360
        west += 360

    LOG.debug("_reduced_grid_indices %s", (name, north, west, south, east))

    accumulated_pls = [0]
    for p in pl:
        accumulated_pls.append(accumulated_pls[-1] + p)

    for i, lons, we, lat in _reduced_longitudes(name, north, west, south, east):
        # LOG.debug(
        #     "we %s %s %s %s %s s=%s",
        #     lat,
        #     we,
        #     lons,
        #     west,
        #     west + we * lons,
        #     int(west / we + 0.5),
        # )
        start = int(west / we + 0.5) + accumulated_pls[i]
        yield (start, start + lons)


@cached_function
def reduced_grid_indices(name, north, west, south, east):
    return list(_reduced_grid_indices(name, north, west, south, east))


@cached_function
def gaussian_number_of_values(name, north, west, south, east):
    return _reduced_number_of_values(name, north, west, south, east)


def latlon_width_heigth(north, west, south, east, we, sn, title):

    a = grid_rounding((north - south) / sn)
    if int(a) != a:
        raise ValueError(
            "South-north increment %g does not match north=%g and south=%g. (%s)"
            % (
                sn,
                north,
                south,
                title,
            )
        )

    b = grid_rounding((east - west) / we)
    if int(b) != b:
        raise ValueError(
            "West-east increment %g does not match west=%g and east=%g. (%s)"
            % (
                we,
                west,
                east,
                title,
            )
        )

    LOG.debug(
        "latlon_width_heigth %s/%s/%s/%s %s/%s %s x %s",
        north,
        west,
        south,
        east,
        we,
        sn,
        int(a + 1),
        int(b + 1),
    )

    return int(a + 1), int(b + 1)


def latlon_number_of_points(north, west, south, east, we, sn, title):
    a, b = latlon_width_heigth(north, west, south, east, we, sn, title)
    return a * b


def latlon_adjust_area(north, west, south, east, we, sn, title):

    # MIR considers the bottom-left point as the reference of the area

    old = east
    while east < west:
        log_warning_once(
            LOG,
            "West boundary %s is greater than east boundary %s. (%s)",
            west,
            east,
            title,
        )
        east += 360

    while east - west > 360:
        log_warning_once(
            LOG,
            "Request covers more than 360 degrees. West boundary is %s, east boundary is %s. (%s)",
            west,
            east,
            title,
        )
        east -= 360

    if east != old:
        log_warning_once(
            LOG,
            "Adjusting east boundary from %g to %g. (%s)",
            old,
            east,
            title,
        )

    a = grid_rounding((north - south) / sn)
    if a != int(a):
        new = grid_rounding(south + sn * int(a))
        log_warning_once(
            LOG,
            "South-north increment %g does not match south=%g and north=%g. (%s)",
            sn,
            south,
            north,
            title,
        )
        log_warning_once(
            LOG,
            "Adjusting north boundary from %g to %g. (%s)",
            north,
            new,
            title,
        )
        north = new

    a = grid_rounding((north - south) / sn)
    if a != int(a):
        new = grid_rounding(south + sn * int(a))
        log_warning_once(
            LOG,
            "South-north increment %g does not match south=%g and north=%g. (%s)",
            sn,
            south,
            north,
            title,
        )
        log_warning_once(
            LOG,
            "Adjusting north boundary from %g to %g. (%s)",
            north,
            new,
            title,
        )
        north = new

    a = grid_rounding((east - west) / we)
    if a != int(a):
        new = grid_rounding(west + we * int(a))
        log_warning_once(
            LOG,
            "West-east increment %g does not match west=%g and east=%g. (%s)",
            we,
            west,
            east,
            title,
        )
        log_warning_once(
            LOG,
            "Adjusting east boundary from %g to %g. (%s)",
            east,
            new,
            title,
        )
        east = new

    if east - west > 360:
        new = grid_rounding(west + 360 - we)

        log_warning_once(
            LOG,
            "Adjusting west/east boundaries from %g/%g to %g/%g. (%s)",
            west,
            east,
            west,
            new,
            title,
        )
        east = new

    if east - west == 360:
        new = grid_rounding(east - we)
        log_warning_once(
            LOG,
            "Adjusting east boundary from %g to %g. (%s)",
            east,
            new,
            title,
        )
        east = new

    assert east - west < 360, (east, west, title)
    return north, west, south, east


def reduced_latlon_number_of_points(name, north, west, south, east):
    return _reduced_number_of_values(name, north, west, south, east)


def full_reduced_grid(name):
    return _reduced_number_of_values(name, 90, 0, -90, 360)
