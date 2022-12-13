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
from ..resources import config

LOG = logging.getLogger(__name__)


def splitter(requests):
    high_frequency_streams = config("high_frequency_streams")
    high_frequency = set(str(s) for s in set(range(0, 91, 1)) - set(range(0, 91, 3)))

    for r in requests:

        if r.stream in high_frequency_streams:
            yield r.annotate("group", "high-frequency")
            continue

        if r.stream in ("enfo", "waef") and "time" in r.fields:

            highf = []
            other = []

            for p in r.fields["time"]:
                if p in ("0600", "1800"):
                    highf.append(p)
                else:
                    other.append(p)

            if highf:
                yield Request(r, time=tuple(highf)).annotate(
                    "group", "high-frequency"
                ).annotate(
                    "split",
                    "frequency",
                    override="append",
                    only_if=other,
                )

            if other:
                r = Request(r, time=tuple(other)).annotate(
                    "split",
                    "frequency",
                    override="append",
                    only_if=highf,
                )
            else:
                continue

        if "step" in r.fields:

            highf = []
            other = []

            for p in r.fields["step"]:
                if p in high_frequency:
                    highf.append(p)
                else:
                    other.append(p)

            if highf:
                yield Request(r, step=tuple(highf)).annotate(
                    "group", "high-frequency"
                ).annotate(
                    "split",
                    "frequency",
                    override="append",
                    only_if=other,
                )

            if other:
                yield Request(r, step=tuple(other)).annotate(
                    "split",
                    "frequency",
                    override="append",
                    only_if=highf,
                )
        else:
            yield r
