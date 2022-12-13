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
    spherical_harmonics = config("spherical_harmonics")
    spherical_harmonics_param = set(spherical_harmonics["param"])
    spherical_harmonics_levtype = set(spherical_harmonics["levtype"])

    for r in requests:

        if r.fields.get("levtype", ["off"])[0] in spherical_harmonics_levtype:

            sh = []
            gg = []

            for p in r.fields["param"]:
                if p in spherical_harmonics_param:
                    sh.append(p)
                else:
                    gg.append(p)

            if sh:
                yield Request(r, param=tuple(sh)).annotate(
                    "split",
                    "shgg",
                    override="append",
                    only_if=gg,
                )

            if gg:
                yield Request(r, param=tuple(gg)).annotate(
                    "split",
                    "shgg",
                    override="append",
                    only_if=sh,
                )
        else:
            yield r
