#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

from .resources import resource
from .utils import check_subset_name
from .utils import iterate_request
from .utils import log_warning_once

LOG = logging.getLogger(__name__)


class ProductSet:
    def __init__(
        self,
        name,
        description,
        mars,
        set,
        subset,
        same=None,
        order=0,
        free_data=[],
        free_with=[],
        frequency=365,
        ic_frequency=None,
        deliveries_per_dow=52,
        comment=None,
    ):

        check_subset_name(name)
        check_subset_name(subset)

        self.name = name
        self.description = description
        self.mars = mars
        self.order = order
        self.set = set
        self.subset = subset
        self.free_with = free_with
        self.frequency = frequency
        self.ic_frequency = ic_frequency
        self.deliveries_per_dow = deliveries_per_dow

        if deliveries_per_dow is not None:
            diff = abs(deliveries_per_dow * 7 - frequency)
            if diff > 1:
                log_warning_once(
                    LOG,
                    f"Product set {name} has {deliveries_per_dow} deliveries"
                    f" per day of week but frequency {frequency}"
                    f" ({deliveries_per_dow} x 7 = {deliveries_per_dow * 7}), diff={diff}",
                    raise_exception=ValueError,
                )

        if isinstance(free_data, dict):
            free_data = [free_data]

        self.free_data = []
        for f in free_data:
            for flat in iterate_request(f):
                self.free_data.append({k: (v,) for k, v in flat.items()})

    def __repr__(self):
        return f"[{self.name},{self.description}]"

    @property
    def title(self):
        return f"Product set {self.name}: {self.description}"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.order < other.order


def get_all_sets():
    result = []
    for k, v in resource("sets").items():
        result.append(ProductSet(k, **v))

    return result
