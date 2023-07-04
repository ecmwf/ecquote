#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from ecquote.cart import Cart


def test_efi():
    cart = Cart.from_strings(
        """
   stream=eefo,
   type=efi,
   param=2ti,
   time=0000,
   levtype=sfc,
   step=0-120/
        0-168/
        0-24/
        0-240/
        0-72/
        12-132/
        12-36/
        12-84/
        24-144/
        24-48/
        24-96/
        36-108/
        36-156/
        36-60/
        48-120/
        48-168/
        48-72/
        60-132/
        60-180/
        60-84/
        72-144/
        72-192/
        72-96/
        84-108/
        84-156/
        84-204/
        96-120/
        96-168/
        96-216/
        96-264/
        108-132/
        108-180/
        108-228/
        120-144/
        120-192/
        132-156/
        132-204/
        144-168/
        144-216/
        156-180/
        156-228/
        168-336/
        264-432/
        336-504/
        432-600/
        504-672/
        600-768/
        672-840/
        768-936/
        840-1008/
        936-1104

   """
    )

    cart.costing()


if __name__ == "__main__":
    test_efi()
