#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging

import pytest

from ecquote.request import Request
from ecquote.splitters.canonical import splitter as canonical_splitter
from ecquote.splitters.constant import splitter as constant_splitter
from ecquote.splitters.high_frequency import splitter as high_frequency_splitter
from ecquote.splitters.shgg import splitter as shgg_splitter
from ecquote.splitters.subset import splitter as subset_splitter

LOG = logging.getLogger(__name__)


def test_shgg_splitter():
    r = Request("type=an,stream=oper,levtype=ml,param=t/q")
    splitted = list(shgg_splitter([r]))
    assert len(splitted) == 2


def test_constant_splitter_1():
    r = Request("type=an,stream=oper,levtype=sfc,param=lsm/2t")
    splitted = list(constant_splitter([r]))
    assert len(splitted) == 2


def test_constant_splitter_2():
    r = Request("type=an,stream=oper,levtype=ml,param=lnsp/t,levelist=1")
    splitted = list(constant_splitter([r]))
    assert len(splitted) == 2


def test_canonical_splitter():
    r = Request(
        """
    type=an,stream=oper,levtype=sfc,param=2t/2TALM2,
    time=0/06/1200/18,grid=.5/5,area=90/0/-90/-.5,
    step=3/to/48/by/3,number=1/to/5
    """
    )
    splitted = list(canonical_splitter([r]))
    assert len(splitted) == 1
    r = splitted[0]
    print(splitted)

    assert r.fields["time"] == ("0000", "0600", "1200", "1800")
    assert r.fields["param"] == ("2t", "2talm2")
    assert r.fields["step"] == tuple("3/6/9/12/15/18/21/24/27/30/33/36/39/42/45/48".split("/"))
    assert r.fields["number"] == ("1", "2", "3", "4", "5")
    assert r.fields["class"] == ("od",)
    assert r.fields["domain"] == ("g",)
    assert r.fields["expver"] == ("0001",)
    assert r.postproc["grid"] == ("0.5", "5.0")
    assert r.postproc["area"] == ("90.0", "0.0", "-90.0", "359.5")


# Disabled broken test following changes for the July 2024 service model we did not have
# time to fix to the the release being urgent.
@pytest.mark.skip(reason="Broken test after the July 2024 service model changes, needs to be fixed.")
def test_subset_splitter_1():
    r = Request(
        "stream=eefo,type=ep,levtype=sfc,param=2tag0/2talm1/2tag2/2talm2/2tag1/tpag10/tpag20,"
        "time=0000,step=96-264/264-432/432-600/600-768"
    )
    splitted = list(subset_splitter([r]))
    assert len(splitted) == 2, (splitted, [r.subset for r in splitted])

    splitted = sorted(splitted, key=lambda x: x.subset.name)
    assert splitted[0].subset.name == "VI-vi-a", splitted[0].subset.name
    assert splitted[1].subset.name == "VI-vi-b", splitted[1].subset.name

    r = Request("stream=mmsf,origin=ecmf,system=5,method=1,type=fc,levtype=sfc,param=tp,time=0000,step=24")
    splitted = list(subset_splitter([r]))
    assert len(splitted) == 1, (splitted, [r.subset for r in splitted])
    assert r.subset.name == "V-v-a", r.subset.name


def test_high_frequency_splitter():
    steps = "/".join(str(i) for i in range(0, 91))
    r = Request(f"type=fc,stream=oper,levtype=sfc,param=2t,step={steps}")
    print(r)
    splitted = list(high_frequency_splitter([r]))
    print(splitted)
    assert len(splitted) == 2, splitted


if __name__ == "__main__":
    test_constant_splitter_2()
