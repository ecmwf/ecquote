#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
from collections import defaultdict

from ..utils import progress
from .free_sets import split_paid_free_set

LOG = logging.getLogger(__name__)


def find_freebies(subset, freebies, requests):
    result = []
    for r in requests:
        p, f = split_paid_free_set(
            r,
            freebies,
            subset.name,
            ignore=["number", "leg", "dataset"],
        )
        result.append((r, p, f))

    return result


def splitter(requests):
    requests = list(progress(requests, "Split"))
    paid_requests = []
    free_requests = []

    matches = defaultdict(list)
    for r in requests:
        matches[r.freebie_matching()].append(r)

    n = 0
    for k, v in progress(matches.items(), "Freebies"):
        more = True
        n += 1
        while more:
            more = False
            for r in tuple(v):
                subset = r.subset
                freebies = r.freebies()

                if freebies:
                    result = find_freebies(subset, freebies, v)
                    for r, p, f in result:
                        if f:
                            v.remove(r)
                            v += p
                            free_requests += f

                            if p:
                                more = True
                                # print("more", n, len(v))

    for k, v in matches.items():
        paid_requests += v

    if False:
        assert sum(r.number_of_fields() for r in requests) == sum(r.number_of_fields() for r in paid_requests) + sum(
            r.number_of_fields() for r in free_requests
        ), (
            sum(r.number_of_fields() for r in requests),
            sum(r.number_of_fields() for r in paid_requests) + sum(r.number_of_fields() for r in free_requests),
            sum(r.number_of_fields() for r in paid_requests),
            sum(r.number_of_fields() for r in free_requests),
        )

    yield from (x.annotate("split", "freebies", override="append", only_if=free_requests) for x in paid_requests)
    yield from (x.annotate("split", "freebies", override="append", only_if=paid_requests) for x in free_requests)
