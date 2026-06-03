#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from types import SimpleNamespace

import pytest

from ecquote.grib import grib2_section3, grib2_section5
from ecquote.repres import REPRES, UnstructuredGrid

N_POINTS = 1025


class DummyRequest:
    def __init__(self, number_of_fields=3, repres_name="unstructured_grid"):
        self._number_of_fields = number_of_fields
        self.repres = SimpleNamespace(name=repres_name)

    def number_of_fields(self):
        return self._number_of_fields


@pytest.fixture
def grid():
    req = DummyRequest(number_of_fields=3)
    return UnstructuredGrid(req, type="unstructured_grid", numberOfDataPoints=N_POINTS)


def test_name():
    assert UnstructuredGrid.name == "unstructured_grid"


def test_registered_in_repres():
    assert REPRES["unstructured_grid"] is UnstructuredGrid


def test_encoded_values(grid):
    assert grid.encoded_values() == (N_POINTS, 0)


def test_number_of_points(grid):
    assert grid.number_of_points() == N_POINTS


def test_number_of_pl(grid):
    assert grid.number_of_pl() == 0


def test_factor_A(grid):
    assert grid.factor_A() == 1


def test_factor_R(grid):
    assert grid.factor_R(None) == 1


def test_is_global(grid):
    assert grid.is_global() is True


def test_used_when_computing_free_data_grid(grid):
    assert grid.used_when_computing_free_data_grid() is True


def test_details(grid):
    assert str(N_POINTS) in grid.details()
    assert "unstructured" in grid.details()


def test_number_of_chargeable_items(grid):
    assert grid.number_of_chargeable_items(grid.request) == 3


def test_explain_items(grid):
    assert "3" in grid.explain_items(grid.request)


def test_grib2_section3():
    req = DummyRequest()
    assert grib2_section3(req, 0, 0, 16) == 19


def test_grib2_section5():
    req = DummyRequest()
    assert grib2_section5(req, 0, 0, 16) == 21
