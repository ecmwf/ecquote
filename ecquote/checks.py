#!/usr/bin/env python3
# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

from .resources import resource

LOG = logging.getLogger(__name__)


DELIVERIES = {
    "eefh": 25,
    "eehs": 25,
    "weeh": 25,
    "wehs": 25,
    "wees": 25,
    "enfh": 12,
    "efhs": 12,
    "enwh": 12,
    "msmm": None,
    "mmsa": None,
    "swmm": None,
    "mmsf": None,
    "wasf": None,
}


def check_sets():
    LOG.info("Checking product sets")
    sets = resource("sets")
    for name, conf in sets.items():
        mars = conf["mars"]
        if "stream" not in mars:
            LOG.warning("%s", f"Product set {name} does not have a stream: {conf}")
        streams = mars.get("stream", "oper")
        if not isinstance(streams, list):
            streams = [streams]

        deliveries_per_dow = conf.get("deliveries_per_dow", 52)
        frequency = conf.get("frequency", 365)

        if deliveries_per_dow is not None:
            diff = abs(deliveries_per_dow * 7 - frequency)
            if diff > 1:
                LOG.error(
                    "%s",
                    f"Product set {name} has {deliveries_per_dow} deliveries"
                    f" per day of week but frequency {frequency}"
                    f" ({deliveries_per_dow} x 7 = {deliveries_per_dow * 7}), diff={diff}",
                )

        for stream in streams:
            if deliveries_per_dow != DELIVERIES.get(stream, 52):
                LOG.error(
                    "%s",
                    f"Deliveries per day of week should be {DELIVERIES.get(stream, 52)} for stream {stream}: {name}",
                )


def validate():
    check_sets()
