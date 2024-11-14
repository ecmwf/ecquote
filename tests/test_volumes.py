#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

from ecquote.request import Request

LOG = logging.getLogger(__name__)

percent = 0.005


def compare(a, b):
    assert abs(a - b) / b <= percent


def dont_test_volumes():
    compare(
        Request("levtype=ml,param=q,stream=oper,type=an").estimated_volume(),
        13205780,
    )

    compare(
        Request("levtype=ml,param=t,stream=oper,type=an").estimated_volume(),
        3281554,
    )

    compare(
        Request("levtype=pl,param=q,stream=oper,type=an").estimated_volume(),
        13204676,
    )

    compare(
        Request("levtype=pl,param=t,stream=oper,type=an").estimated_volume(),
        3280450,
    )

    compare(
        Request("levtype=sfc,param=2t,stream=oper,type=an").estimated_volume(),
        13204676,
    )

    compare(
        Request("levtype=sfc,param=2t,stream=oper,type=an,grid=1/1").estimated_volume(),
        130516,
    )

    compare(
        Request("levtype=sfc,param=2t,stream=oper,type=an,grid=1/1,area=50/0/0/50").estimated_volume(),
        5398,
    )


if __name__ == "__main__":
    pass
