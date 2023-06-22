#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

from ..matching import Matcher
from ..sets import ProductSet
from ..utils import capture_warnings

LOG = logging.getLogger(__name__)


def splitter(requests):
    def multiple(sets):
        return sets

    sets_matcher = Matcher(
        "sets",
        ProductSet,
        multiple=multiple,
    )

    # Simply annotate with subset
    for request in requests:
        with capture_warnings(request):
            subset = sets_matcher.get_match(request)
            if isinstance(subset, list):
                for r, s in subset:
                    r.fields["dataset"] = (s.name,)
                    r.annotate("subset", s).annotate(
                        "split",
                        "subset",
                        override="append",
                    )
                    yield r
            else:
                request.fields["dataset"] = (subset.name,)
                request.annotate("subset", subset)
                yield request
