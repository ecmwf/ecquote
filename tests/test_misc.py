#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

from ecquote.request import Request
from ecquote.splitters import prepare_request

FREQUENCIES = (
    ("type=an,levtype=sfc,stream=oper", 365),
    ("type=cf,levtype=sfc,stream=enfo,step=24", 365),
    ("type=cf,levtype=sfc,stream=enfo,step=384", 104),
    ("type=cf,levtype=sfc,stream=enfo,step=24,use=monday", 52),
    ("type=cf,levtype=sfc,stream=enfo,step=384,use=monday", 52),
    ("type=cf,levtype=sfc,stream=enfo,step=24,use=thursday", 52),
    ("type=cf,levtype=sfc,stream=enfo,step=384,use=thursday", 52),
    ("type=cf,levtype=sfc,stream=enfo,step=24,use=monday/thursday", 104),
    ("type=cf,levtype=sfc,stream=enfo,step=384,use=monday/thursday", 104),
    ("type=efi,levtype=sfc,stream=enfo,step=0-24", 365),
    ("type=sot,levtype=sfc,stream=enfo,step=0-24", 365),
    ("type=efi,levtype=sfc,stream=enfo,step=0-24", 365),
    ("type=efi,levtype=sfc,stream=enfo,step=840-1008", 104),
    ("type=sot,levtype=sfc,stream=enfo,step=0-24", 365),
    ("type=sot,levtype=sfc,stream=enfo,step=840-1008", 104),
)


@pytest.mark.parametrize("test", FREQUENCIES)
def test_frequency(test):
    req, value = test
    r = prepare_request(Request(req))
    assert r.frequency() == value


BITS_PER_VALUE = (("type=an,levtype=sfc,stream=oper,param=2t", [12]),)


@pytest.mark.parametrize("test", BITS_PER_VALUE)
def test_bits_per_value(test):
    req, value = test
    r = prepare_request(Request(req))
    assert r.repres.bits_per_value() == value


VOLUMES = (("type=an,levtype=sfc,stream=oper,param=2t", 9904836),)


@pytest.mark.parametrize("test", VOLUMES)
def test_estimated_volume(test):
    req, value = test
    r = prepare_request(Request(req))
    assert r.estimated_volume() == value
