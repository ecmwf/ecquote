#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

LOG = logging.getLogger(__name__)


def splitter(requests, groups):
    if not isinstance(groups, (list, tuple)):
        groups = groups.split("-")

    for r in requests:
        yield r.annotate("group", "-".join(r.fields[g][0] for g in groups))
