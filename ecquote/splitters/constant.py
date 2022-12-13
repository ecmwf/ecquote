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
    rules = config("constant_fields")
    for r in requests:
        match = False
        if r.type not in ("wp", "tf"):
            for rule in rules:

                if not isinstance(rule["param"], (tuple, list)):
                    rule["param"] = [rule["param"]]

                if r.fields.get("levtype", ["off"])[0] == rule["levtype"]:

                    constant = []
                    variable = []

                    for p in r.fields.get("param", []):
                        if p in rule["param"]:
                            constant.append(p)
                        else:
                            variable.append(p)

                    if constant:
                        yield Request(r, param=tuple(constant)).annotate(
                            "free", "constant"
                        ).annotate(
                            "split",
                            "constant",
                            override="append",
                            only_if=variable,
                        )

                        if variable:
                            yield Request(r, param=tuple(variable)).annotate(
                                "split",
                                "constant",
                                override="append",
                            )
                        match = True
                        break

        if not match:
            yield r
