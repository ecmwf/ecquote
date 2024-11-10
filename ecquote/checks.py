#!/usr/bin/env python3
# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import functools
import itertools
import logging
import re
from contextlib import contextmanager

from .resources import resource

LOG = logging.getLogger(__name__)


DELIVERIES = {
    'eefo': 52,
    'weef': 25,
    'eefh': 52,
    'eehs': 52,
    'weeh': 25,
    'wehs': 25,
    'wees': 25,
    'enfh': 12,
    'efhs': 12,
    'enwh': 12,
}

def check_sets():
    LOG.info("Checking product sets")
    sets = resource('sets')
    for name, conf in sets.items():
        print(name, conf)
        mars = conf['mars']
        stream = mars['stream']
        assert isinstance(stream, str), f"Stream is not a string: {stream} {name}"

        deliveries_per_dow = conf.get('deliveries_per_dow', 52)
        frequency = conf.get('frequency', 365)

        diff = abs(deliveries_per_dow * 7 - frequency)
        if diff > 1:
            ValueError(
                f"Product set {name} has {deliveries_per_dow} deliveries"
                f" per day of week but frequency {frequency}"
                f" ({deliveries_per_dow} x 7 = {deliveries_per_dow * 7}), diff={diff}",
            )

        if deliveries_per_dow != DELIVERIES.get(stream, 52):
            ValueError(
                f"Deliveries per day of week should be {DELIVERIES.get(stream, 52)} for stream {stream}: {name}",
            )



def validate():
    LOG.info("Checking product sets")
    check_sets()
