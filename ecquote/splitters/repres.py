#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import glob
import logging
import os

from ..matching import Matcher
from ..resources import config
from ..utils import capture_warnings

LOG = logging.getLogger(__name__)


def error(request):

    if not os.path.exists("tests/representations"):
        return

    r = []
    for k, v in sorted(request.fields.items()):
        if k == "dataset":
            continue
        v = "/".join(str(x) for x in v)
        r.append(f"{k}={v}")
    text = ",\n".join(r) + "\n"

    for p in glob.glob("tests/representations/????.req"):
        with open(p) as f:
            if text == f.read():
                return

    n = len(glob.glob("tests/representations/????.req"))
    with open("tests/representations/%04d.req" % (n,), "w") as f:
        f.write(text)


def splitter(requests):
    # Find multi-repres requests
    # This is the case of EFI and SOT in the extended forecasts (VI-vii-a and VI-vii-b)
    # when the resultion changes from O640 to O320 after step 360

    def single(_, **r):
        return r["repres"]

    def multiple(matches):
        return matches

    default_representation = config("default_representation")

    if default_representation:
        repres_matcher = Matcher(
            "representations",
            single,
            multiple=multiple,
            default=lambda *args, **kwargs: "latlon",
        )
    else:
        repres_matcher = Matcher(
            "representations",
            single,
            multiple=multiple,
            error=error,
        )

    for request in requests:
        with capture_warnings(request):
            matches = repres_matcher.get_match(request)

            if isinstance(matches, list):
                for r, _ in matches:
                    yield r.annotate("split", "repres", override="append")
            else:
                yield request
