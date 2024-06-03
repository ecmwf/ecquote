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
    ("type=an,levtype=sfc,stream=oper", 365, 365),
    ("type=fc,levtype=sfc,stream=oper", 365, 365),
    ("type=an,levtype=sfc,stream=scda", 365, 365),
    ("type=fc,levtype=sfc,stream=scda", 365, 365),
    ("type=cf,levtype=sfc,stream=enfo,step=24", 365, 365),
    ("type=cf,levtype=sfc,stream=eefo,step=24,use=monday", 52, 52),
    ("type=cf,levtype=sfc,stream=eefo,step=24,use=thursday", 52, 52),
    ("type=cf,levtype=sfc,stream=eefo,step=24,use=monday/thursday", 104, 104),
    ("type=cf,levtype=sfc,stream=eefo,step=24,use=wednesday/sunday", 104, 104),
    ("type=cf,levtype=sfc,stream=eefo,step=24,use=monday/wednesday/sunday", 156, 104),
    ("type=pf,levtype=sfc,stream=enfo,step=24", 365, 365),
    ("type=pf,levtype=sfc,stream=eefo,step=24", 365, 104),
    ("type=pf,levtype=sfc,stream=eefo,step=24,use=monday", 52, 52),
    ("type=pf,levtype=sfc,stream=eefo,step=24,use=thursday", 52, 52),
    ("type=pf,levtype=sfc,stream=eefo,step=24,use=monday/thursday", 104, 104),
    ("type=pf,levtype=sfc,stream=eefo,step=24,use=wednesday/sunday", 104, 104),
    ("type=pf,levtype=sfc,stream=eefo,step=24,use=monday/wednesday/sunday", 156, 104),
    ("type=pf,levtype=sfc,stream=eefo,step=24,use=tuesday/friday/sunday", 156, 104),
    # any step ranges must have a use=day-of-the-week with it
    # ("type=taem,param=2t,levtype=sfc,stream=eefo,step=0-168", 365, 104)
    ("type=taem,param=2t,levtype=sfc,stream=eefo,step=0-168,use=monday", 52, 52),
    ("type=taem,param=2t,levtype=sfc,stream=eefo,step=0-168,use=thursday", 52, 52),
    (
        "type=taem,param=2t,levtype=sfc,stream=eefo,step=0-168,use=monday/thursday",
        104,
        104,
    ),
    (
        "type=taem,param=2t,levtype=sfc,stream=eefo,step=0-168,use=wednesday/sunday",
        104,
        104,
    ),
    (
        "type=taem,param=2t,levtype=sfc,stream=eefo,step=0-168,use=monday/wednesday/sunday",
        156,
        104,
    ),
    ("type=fcmean,param=sda,levtype=sfc,stream=eefo,step=0-168,use=monday", 52, 52),
    (
        "type=fcmean,param=sda,levtype=sfc,stream=eefo,step=0-168,use=monday/thursday",
        104,
        104,
    ),
    (
        "type=fcmean,param=sda,levtype=sfc,stream=eefo,step=0-168,use=monday/wednesday/thursday",
        156,
        104,
    ),
)


@pytest.mark.parametrize("test", FREQUENCIES)
def test_frequency(test):
    req, f, g = test
    r = prepare_request(Request(req))
    assert r.frequency() == f
    assert r.chargeable_frequency() == g


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
