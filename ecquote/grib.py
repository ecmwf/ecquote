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


def round_up(x, n):
    return int((x + n - 1) / n) * n


def grib2_section0(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
):
    # GRIB
    return 16


def grib2_section1(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
):
    # date, time
    return 21


def grib2_section2(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
):
    # mars labeling
    return 17


def grib2_section3(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
):
    # section3: grid definition

    def latlon():
        if "rotation" in request.postproc:
            return 84
        return 72

    def gaussian():
        return 72 + request.number_of_pl() * 2

    def reduced_ll():
        return 72 + request.number_of_pl() * 2

    def spectral():
        return 28

    return dict(
        spectral=spectral,
        gaussian=gaussian,
        latlon=latlon,
        reduced_ll=reduced_ll,
    )[request.repres.name]()


def grib2_section4(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
):
    def ml():
        return 34 + (request.number_of_model_levels() + 1) * 2 * 4

    def other():
        return 34

    return dict(
        ml=ml,
    ).get(request.levtype, other)()


def grib2_section5(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
):
    return dict(
        spectral=35,
        gaussian=21,
        latlon=21,
        reduced_ll=21,
    )[request.repres.name]


def grib2_section6(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
):
    LOG.debug(
        "grib2_section6 number_of_values=%s number_of_missing_values=%s",
        number_of_values,
        number_of_missing_values,
    )

    # 6 + bits, bitmap
    if number_of_missing_values > 0:
        bytes_bitmap = round_up(number_of_values + number_of_missing_values, 8) // 8
    else:
        bytes_bitmap = 0
    return 6 + bytes_bitmap


def grib2_section7(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
):
    # section7: 5 + values, values    volume = 0

    LOG.debug(
        "grib2_section7 number_of_values=%s bits_per_value=%s",
        number_of_values,
        bits_per_value,
    )

    def simple():
        bytes_values = round_up(number_of_values * bits_per_value, 8) // 8
        return 5 + bytes_values

    def complex():
        # Assumptions:
        #   - JS = 20
        #   - unpackedSubsetPrecision=1 (IEEE 32-bit)

        unpacked_values = (20 + 1) * (20 + 2)

        packed_values = number_of_values - unpacked_values
        bytes_values = (
            round_up(unpacked_values * 32 + packed_values * bits_per_value, 8) // 8
        )
        return 5 + bytes_values

    return dict(spectral=complex).get(request.repres.name, simple)()


def grib2_section8(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
):
    # 7777
    return 4


SECTIONS = {
    2: [
        grib2_section0,
        grib2_section1,
        grib2_section2,
        grib2_section3,
        grib2_section4,
        grib2_section5,
        grib2_section6,
        grib2_section7,
        grib2_section8,
    ]
}


def grib_size(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
    edition=2,
):
    if LOG.isEnabledFor(logging.DEBUG):
        # grib_dump -D q| grep section_length
        LOG.debug(
            "GRIB %s sections %s",
            edition,
            [
                section(
                    request,
                    number_of_values,
                    number_of_missing_values,
                    bits_per_value,
                )
                for section in SECTIONS[edition]
            ],
        )

    return sum(
        section(
            request,
            number_of_values,
            number_of_missing_values,
            bits_per_value,
        )
        for section in SECTIONS[edition]
    )


def grib_sections(
    request,
    number_of_values,
    number_of_missing_values,
    bits_per_value,
    edition=2,
):

    return tuple(
        section(
            request,
            number_of_values,
            number_of_missing_values,
            bits_per_value,
        )
        for section in SECTIONS[edition]
    )
