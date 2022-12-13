#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import csv
import logging

LOG = logging.getLogger(__name__)


def splitter(requests, path, only_category):

    categories = {}
    with open(path) as csvfile:
        cats = set()
        for row in csv.reader(csvfile, delimiter=","):
            categories[row[0]] = row[1:]
            cats.add(row[1])

    if only_category is not None:

        if only_category not in cats:
            print(f"Invalid category [{only_category}]")
            print("Values are:")
            for c in sorted(cats):
                print(f" [{c}]")
            raise ValueError(f"Invalid category [{only_category}]")

    for r in requests:
        tag = r.tag.split(":")[0]
        unknown = f"unknown ({tag})"
        category, user = categories.get(tag, [unknown, unknown])
        if only_category is None or category == only_category:
            yield r.annotate("category", category).annotate("user", user)
