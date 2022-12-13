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

from ..request import Request

LOG = logging.getLogger(__name__)


def splitter(requests):
    # need_leg = config("need_leg")
    for r in requests:

        if r.stream in ("enfo", "waef", "efov") and r.type in ("pf", "cf"):

            use = r.use.get("use", [])
            if "monday" in use or "thursday" in use:
                yield Request(r, leg=(2,))
                continue

            split = defaultdict(list)
            for s in r.fields["step"]:
                try:
                    split[int(s.split("-")[-1]) > 360].append(s)
                except ValueError:
                    # Some legacy requests have ':' instead of '-'
                    split[int(s.split(":")[-1]) > 360].append(s)

            legs = 0
            for leg, which in (("1", False), ("2", True)):
                if len(split[which]):
                    legs += 1

            for leg, which in (("1", False), ("2", True)):
                if len(split[which]):
                    yield Request(r, leg=(leg,), step=tuple(split[which])).annotate(
                        "split",
                        "leg",
                        override="append",
                        only_if=legs > 1,
                    )

        else:
            yield r
