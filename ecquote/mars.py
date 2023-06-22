#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import os

import ecmwfapi


def retrieve(request, target, force=False):
    if os.path.exists(target) and not force:
        return target

    c = ecmwfapi.ECMWFService("mars")
    c.execute(request, target + ".tmp")
    os.rename(target + ".tmp", target)
