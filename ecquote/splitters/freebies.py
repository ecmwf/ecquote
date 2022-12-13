#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging

from ..request import Request
from ..utils import progress
from .free_sets import split_paid_free_set

LOG = logging.getLogger(__name__)


def find_freebies(subset, freebies, requests):
    paid = []
    free = []
    for r in requests:
        p, f = split_paid_free_set(
            r,
            freebies,
            subset.name,
            ignore=["number", "leg", "dataset"],
        )
        paid += p
        free += f

    return paid, free


def splitter(requests):
    requests = list(requests)
    paid_requests = requests
    free_requests = []

    for r in progress(requests):
        subset = r.subset
        freebies = []

        freebies = []
        for f in subset.free_data:
            freebies.append(Request(r, f))

        if freebies:

            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug("freebies for %s", r.summary())
                for i, f in enumerate(freebies):
                    LOG.debug("freebie %s: %s", i, f.summary())

            pp = r.postproc
            user = r.user

            matching = [(p.user == user and p.postproc == pp, p) for p in paid_requests]
            test = [m[1] for m in matching if m[0]]
            rest = [m[1] for m in matching if not m[0]]

            if LOG.isEnabledFor(logging.DEBUG):
                for p in test:
                    LOG.debug("possible freebie  %s", p.summary())

            p, f = find_freebies(subset, freebies, test)
            paid_requests = p + rest
            free_requests += f

    yield from (
        x.annotate("split", "freebies", override="append", only_if=free_requests)
        for x in paid_requests
    )
    yield from (
        x.annotate("split", "freebies", override="append", only_if=paid_requests)
        for x in free_requests
    )
