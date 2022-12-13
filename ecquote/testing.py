#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
import os

from .utils import as_numbers

LOG = logging.getLogger(__name__)


def list_of_tests(script, name, key_to_issue):
    top = os.path.join(os.path.dirname(script), name)
    tests = {}
    for root, _, files in os.walk(top):
        for file in files:
            if file.endswith(".req"):
                full = os.path.join(root, file)
                key = full[len(top) + 1 : -4]
                tests[key] = full

    tst = {}
    for t in tests.keys():
        issue = key_to_issue(t)
        if os.path.exists(issue):
            tst[t] = tests[t]

    # if tst:
    #     return tst

    return tests


def extract_cost(path):
    cost = {}
    with open(path) as f:
        for line in f:
            if line.startswith("# "):
                if "=" in line:
                    key, value = line[2:].strip().split("=")
                    cost[key.strip()] = as_numbers(value.strip())
    return cost
