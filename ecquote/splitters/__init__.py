#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging

from ..resources import config
from .canonical import splitter as canonical_splitter
from .category import splitter as category_splitter
from .constant import splitter as constant_splitter
from .destination import splitter as destination_splitter
from .free_sets import splitter as free_splitter
from .freebies import splitter as freebies_splitter
from .group_by import splitter as group_by_splitter
from .high_frequency import splitter as high_frequency_splitter
from .leg import splitter as leg_splitter
from .repres import splitter as repres_splitter
from .shgg import splitter as shgg_splitter
from .subset import splitter as subset_splitter
from .validate import splitter as validate_splitter

LOG = logging.getLogger(__name__)

# TODO: add the logic in the config file


def first_splitters(requests, categories=None, category=None, **kwargs):

    s = requests

    s = canonical_splitter(s)
    s = validate_splitter(s)
    s = leg_splitter(s)
    s = shgg_splitter(s)
    s = subset_splitter(s)
    s = repres_splitter(s)

    if categories:
        s = category_splitter(s, categories, category)

    if config("destinations"):
        s = destination_splitter(s)

    return s


def second_splitters(requests, group_by=None, **kwargs):

    s = requests

    if group_by or config("group-by"):
        s = group_by_splitter(s, group_by if group_by else config("group-by"))
    else:
        s = high_frequency_splitter(s)

    s = constant_splitter(s)
    if config("free-open-data"):
        s = free_splitter(
            s,
            "free-open-data",
            # canonical_grid([0.4, 0.4]),
        )
    if config("free-wmo-essential"):
        s = free_splitter(
            s,
            "free-wmo-essential",
            # canonical_grid([0.5, 0.5]),
        )

    if config("free-data"):
        s = free_splitter(
            s,
            config("free-data"),
        )

    s = freebies_splitter(s)
    return s


def prepare_request(request):
    request = list(first_splitters([request]))
    assert len(request) == 1, request
    return request[0]
