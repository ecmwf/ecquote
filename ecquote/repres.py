#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging
import re

from .grib import grib_sections, grib_size
from .grid import (
    gaussian_number_of_values,
    latlon_adjust_area,
    latlon_number_of_points,
    latlon_width_heigth,
    less_or_equal,
    number_of_pl,
    reduced_latlon_number_of_points,
)
from .matching import Matcher
from .resources import config
from .utils import bytes, cached_method, log_warning_once, plural

LOG = logging.getLogger(__name__)


def round_up(x, n):
    return int((x + n - 1) / n) * n


HEADERS = {1: 1024, 2: 108}


####################################
accuracy_matcher = Matcher("accuracy", lambda _, value, **kwargs: value)

####################################

representation_matcher = Matcher("representations", lambda _, **r: r["repres"])

# https://confluence.ecmwf.int/display/UDOC/What+is+the+connection+between+the+spectral+truncation+and+the+Gaussian+grids+-+Metview+FAQ


def current_model_grid(request):
    repres = representation_matcher.get_match(request)

    grid = None
    gaussian = None
    resol = None

    if "reduced_ll" in repres:
        grid = repres["reduced_ll"]

    if "gaussian" in repres:
        gaussian = repres["gaussian"]
        assert re.match(r"[FON]\d+", gaussian), gaussian

        gaussian = int(gaussian[1:])
        grid = 90 / gaussian

    if "grid" in repres:
        grid = max(repres["grid"])

    if "resol" in repres:
        resol = repres["resol"]

    if gaussian is None and resol is not None:
        gaussian = resol + 1

    if grid is None and gaussian is not None:
        grid = 90 / gaussian

    return grid, gaussian, resol


####################################
ACCURACIES = (8, 9, 10, 11, 12, 13, 16, 24)


class PgenAccuracy:
    def bits(self, param, request):
        from .request import Request

        bits = accuracy_matcher.get_match(Request(param=(param,)))
        assert bits in ACCURACIES, (bits, param)
        return bits


class Accuracy:
    def __init__(self, accuracy):
        self.accuracy = accuracy
        assert accuracy in ACCURACIES, accuracy

    def bits(self, param, request):
        return self.accuracy

    def __repr__(self):
        return str(self.accuracy)


class AccuracyAV:
    def __init__(self):
        pass

    def bits(self, param, request):
        log_warning_once(
            LOG,
            "Accuracy AV is not yet supported (%s), assuming 16 bits",
            request.tag,
        )
        return 16

    def __repr__(self):
        return "av"


####################################


class Repres:
    def __init__(self, request, **kwargs):
        LOG.debug("Repres %s %s %s", self.__class__.__name__, kwargs, request)
        self.request = request
        for k, v in kwargs.items():
            setattr(self, k, v)

    def set_grid(self, we, sn):
        log_warning_once(
            LOG,
            "Setting grid=%s/%s for %s is ignored. (%s)",
            we,
            sn,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def set_area(self, area):
        log_warning_once(
            LOG,
            "Setting area=%s for %s is ignored. (%s)",
            area,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def set_location(self, location):
        log_warning_once(
            LOG,
            "Setting location=%s for %s is ignored. (%s)",
            location,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def set_gaussian(self, gaussian):
        log_warning_once(
            LOG,
            "Setting gaussian=%s for %s is ignored. (%s)",
            gaussian,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def set_resol(self, resol):
        log_warning_once(
            LOG,
            "Setting resol=%s for %s is ignored. (%s)",
            resol,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def set_point(self, point):
        log_warning_once(
            LOG,
            "Setting point=%s for %s is ignored. (%s)",
            point,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def set_accuracy(self, accuracy):
        log_warning_once(
            LOG,
            "Setting accuracy=%s for %s is ignored. (%s)",
            accuracy,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def set_bitmap(self, bitmap):
        log_warning_once(
            LOG,
            "Setting bitmap=%s for %s is ignored. (%s)",
            bitmap,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def set_frame(self, frame):
        log_warning_once(
            LOG,
            "Setting frame=%s for %s is ignored. (%s)",
            frame,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def set_rotation(self, rotation):
        log_warning_once(
            LOG,
            "Setting rotation=%s for %s is ignored. (%s)",
            rotation,
            self.__class__.__name__,
            self.request.tag,
        )
        return self

    def encoded_values(self):
        log_warning_once(
            LOG,
            "Ignoring encoded_values calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
        )
        return 0, 0

    def number_of_pl(self):
        log_warning_once(
            LOG,
            "Ignoring number_of_pl calculation for type %s (%s)",
            self.__class__.__name__,
            self.request,
        )
        return 0

    def number_of_model_levels(self):
        log_warning_once(
            LOG,
            "Ignoring number_of_model_levels calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
        )
        return 0

    def number_of_chargeable_items(self, request):
        log_warning_once(
            LOG,
            "Ignoring number_of_chargeable_items calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
        )
        return 0

    def factor_A(self):
        log_warning_once(
            LOG,
            "Ignoring factor_A calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
        )
        return 1

    def factor_R(self, reference):
        log_warning_once(
            LOG,
            "Ignoring factor_R calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
        )
        return 1

    def reference_grid(self, reference):
        log_warning_once(
            LOG,
            "Ignoring reference_grid calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
        )
        return "?"

    def apply_bitmap(self):
        log_warning_once(
            LOG,
            "Ignoring apply_bitmap calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
        )
        return 0

    def apply_frame(self):
        log_warning_once(
            LOG,
            "Ignoring apply_frame calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
        )
        return 0

    def wave_missing_values_ratio(self):
        log_warning_once(
            LOG,
            "Ignoring wave_missing_values_ratio calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
            raise_exception=ValueError,
        )
        return 1

    def finalise(self):
        return self

    def estimated_volume(self):
        npoints, nmissing = self.encoded_values()

        number_of_fields = self.request.number_of_fields()
        params = self.request.params

        number_of_fields_per_param = number_of_fields // len(params)
        assert number_of_fields_per_param * len(params) == number_of_fields
        volume = 0

        debug = LOG.isEnabledFor(logging.DEBUG)
        if debug:
            LOG.debug(
                "%s.estimated_volume number_of_fields=%s param=%s accuracy=%s",
                self,
                number_of_fields,
                params,
                self.accuracy,
            )

        for param in params:
            size = grib_size(
                request=self.request,
                number_of_values=npoints,
                number_of_missing_values=nmissing,
                bits_per_value=self.accuracy.bits(param, self.request),
                edition=2,
            )

            if debug:
                LOG.debug(
                    "%s.estimated_volume param=%s size=%s (%s) number_of_fields_per_param=%s",
                    self,
                    param,
                    size,
                    bytes(size),
                    number_of_fields_per_param,
                )

            volume += size * number_of_fields_per_param

        if debug:
            LOG.debug("%s.estimated_volume volume=%s (%s)", self, volume, bytes(volume))
        return volume

    def grib_sections(self):
        npoints, nmissing = self.encoded_values()

        number_of_fields = self.request.number_of_fields()
        params = self.request.params

        number_of_fields_per_param = number_of_fields // len(params)
        assert number_of_fields_per_param * len(params) == number_of_fields

        result = []
        for param in params:
            sections = grib_sections(
                request=self.request,
                number_of_values=npoints,
                number_of_missing_values=nmissing,
                bits_per_value=self.accuracy.bits(param, self.request),
                edition=2,
            )

            result.append(sections)

        return result

    def bits_per_value(self):

        number_of_fields = self.request.number_of_fields()
        params = self.request.params

        number_of_fields_per_param = number_of_fields // len(params)
        assert number_of_fields_per_param * len(params) == number_of_fields

        result = []
        for param in params:
            result += [
                self.accuracy.bits(param, self.request)
            ] * number_of_fields_per_param

        return result

    def __repr__(self):
        return self.__class__.__name__

    def details(self):
        log_warning_once(
            LOG,
            "Ignoring details calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
            raise_exception=NotImplementedError,
        )
        return "?"

    def explain_A(self):
        log_warning_once(
            LOG,
            "Ignoring explain_A calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
            raise_exception=NotImplementedError,
        )
        return "?"

    def explain_R(self, reference):
        log_warning_once(
            LOG,
            "Ignoring explain_R calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
            raise_exception=NotImplementedError,
        )
        return "?"

    def explain_items(self, request):
        log_warning_once(
            LOG,
            "Ignoring explain_items calculation for type %s. (%s)",
            self.__class__.__name__,
            self.request,
            raise_exception=NotImplementedError,
        )
        return "?"

    def used_when_computing_free_data_grid(self):
        raise NotImplementedError()


class Field(Repres):
    accuracy = PgenAccuracy()

    def set_accuracy(self, accuracy):
        self.accuracy = accuracy
        return self

    def number_of_chargeable_items(self, request):
        from .request import Request

        steps = request.fields.get("step", (0,))
        if request.is_seasonal():
            steps = tuple(set(int(s) // 24 for s in steps))

        # ECMWF/ACDP/6(05)D decision 12
        items = {"2dfd": 10}
        count = 0
        for p in request.fields["param"]:

            count += Request(
                request,
                param=(p,),
                number=(1,),
                frequency=(1,),
                direction=(1,),
                step=steps,
            ).number_of_fields() * items.get(p, 1)
        return count

    def explain_items(self, request):

        explain = []

        steps = request.fields.get("step", (0,))
        if request.is_seasonal():
            explain.append("for seasonal data, chargeable steps are daily steps.")
            explain.append(plural(len(steps), "hourly step"))
            steps = tuple(set(int(s) // 24 for s in steps))
            explain.append("become")
            explain.append(plural(len(steps), "daily step"))

        bits = []

        if "2dfd" in request.fields["param"]:
            assert len(request.fields["param"]) == 1, "Please code me"
            bits.append("(param 2dfd is 10 items)")

        nice = dict(levelist="level")

        for k, v in request.fields.items():
            if k in ("number", "frequency", "direction"):
                continue
            if k == "step":
                v = steps
            if len(v) > 1:
                p = plural(len(v), nice.get(k, k))
                bits.append(f"({p})")

        if bits:
            explain.append(" * ".join(bits))
        else:
            explain.append("1 field")

        return " ".join(str(e) for e in explain)

    def used_when_computing_free_data_grid(self):
        return True


class Area:
    def __init__(self, north, west, south, east, tag="XXX:XX"):
        if north == south:
            log_warning_once(
                LOG,
                "North and south boundaries are the same %g. (%s)",
                north,
                tag,
            )
        assert north >= south, (north, south, self.request.tag)
        while west > east:
            east += 360

        self.north = north
        self.west = west
        self.south = south
        self.east = east

    def __repr__(self):
        return "%g/%g/%g/%g" % (self.north, self.west, self.south, self.east)

    def bounding_box(self):
        return (self.north, self.west, self.south, self.east)


class Gridded(Field):

    area = Area(90, 0, -90, 360)
    bitmap = None
    frame = None

    def set_grid(self, we, sn):
        self.grid = (we, sn)
        return self

    def set_area(self, area):
        self.area = area
        return self

    def encoded_values(self):

        npoints = self.number_of_points()
        nmissing = 0

        assert self.bitmap is None or self.frame is None

        if self.bitmap:
            n = self.apply_bitmap()
            npoints -= n
            nmissing += n

        if self.frame:
            n = self.apply_frame()
            npoints -= n
            nmissing += n

        if self.request.is_wave():
            # assert self.bitmap is None and self.frame is None
            landsea = self.wave_missing_values_ratio()
            nmissing = int(npoints * (1 - landsea) + 0.5)
            npoints -= nmissing

        return npoints, nmissing

    def set_frame(self, frame):
        self.frame = frame
        return self

    def set_bitmap(self, bitmap):
        self.bitmap = bitmap
        return self

    @cached_method
    def factor_A(self):

        if self.is_global():
            return 1

        n, w, s, e = self.adjusted_area()
        assert n >= s
        assert w <= e
        assert e - w <= 360, (e, w, self.request)
        A = (n - s) * (e - w)

        A = A / (360 * 180)

        return A

    def explain_A(self):
        if self.is_global():
            return "field is global, A=1"

        minimum_area = config("minimum_area")

        n, w, s, e = self.adjusted_area()
        assert n >= s
        assert w <= e
        assert e - w <= 360, (e, w, self.request)
        A = (n - s) * (e - w)
        if A < minimum_area:
            return f"minimum area {minimum_area} / (360 * 180)"

        return f"({n} - {s}) * ({e} - {w}) / (360 * 180)"


class LatLon(Gridded):

    name = "latlon"

    area = Area(90, 0, -90, 360)

    def set_grid(self, we, sn):
        self.grid = (we, sn)
        return self

    def set_area(self, area):
        self.area = area
        return self

    def set_rotation(self, rotation):
        assert isinstance(rotation, Rotation)
        return self

    def set_resol(self, resol):
        # Ignored
        return self

    def set_gaussian(self, gaussian):
        # Ignored
        return self

    @cached_method
    def adjusted_area(self):
        return latlon_adjust_area(
            *self.area.bounding_box(),
            *self.grid,
            self.request.tag,
        )

    def number_of_points(self):

        return latlon_number_of_points(
            *self.adjusted_area(),
            *self.grid,
            self.request.tag,
        )

    def is_global(self):
        north, west, south, east = self.adjusted_area()
        we, sn = self.grid
        return north == 90 and south == -90 and less_or_equal(360, east - west + we)

    def factor_R(self, reference):
        we, sn = self.grid
        grid = min(we, sn)

        model_grid, model_gaussian, model_resol = reference
        LOG.debug("factor_R grid=%s reference=%s", grid, reference)

        return model_grid / grid

    def explain_R(self, reference):
        we, sn = self.grid
        grid = min(we, sn)

        model_grid, model_gaussian, model_resol = reference

        return f"{model_grid} / {grid}"

    def reference_grid(self, reference):
        return reference[0]

    def number_of_pl(self):
        return 0

    def apply_frame(self):
        we, ns = self.grid
        north, west, south, east = self.adjusted_area()
        LOG.debug(
            "Apply frame => %s %s %s %s - %s %s - frame %s",
            north,
            west,
            south,
            east,
            we,
            ns,
            self.frame,
        )

        a, b = latlon_width_heigth(
            north,
            west,
            south,
            east,
            we,
            ns,
            f"frame({self.request.tag})",
        )

        nmissing = (a - 2 * self.frame) * (b - 2 * self.frame)
        if nmissing < 0:
            nmissing = 0

        LOG.debug(
            "Apply frame <= %s %s %s %s - %s %s - nmissing %s",
            north,
            west,
            south,
            east,
            we,
            ns,
            nmissing,
        )

        return nmissing

    def global_area(self):
        return (90, 0, -90, 360 - self.grid[0])

    def wave_missing_values_ratio(self):
        return self.request.land_sea_ratio("mask_regular")

    def details(self):
        return f"grid: {self.grid[0]}/{self.grid[1]}, area: {self.area}"


class Gaussian(Gridded):

    name = "gaussian"

    gaussian = None

    def set_grid(self, we, sn):
        return LatLon(self.request).set_grid(we, sn)

    def set_gaussian(self, gaussian):

        if gaussian[0].isdigit():
            log_warning_once(
                LOG,
                "Invalid gaussian grid '%s', assuming 'F%s'. (%s)",
                gaussian,
                gaussian,
                self.request.tag,
            )
            gaussian = f"F{gaussian}"

        self.gaussian = gaussian
        return self

    def adjust_area(self, north, west, south, east):

        # if east - west == 360:
        #     log_warning_once(
        #         LOG,
        #         "Cannot adjust east boundary of Gaussian %s from %g. (%s)",
        #         self.gaussian,
        #         east,
        #         self.request.tag,
        #     )
        assert east - west <= 360, (east, west, self.request)
        return north, west, south, east

    def adjusted_area(self):
        return self.adjust_area(*self.area.bounding_box())

    @property
    def N(self):
        assert self.gaussian[0] in "FON"
        return int(self.gaussian[1:])

    @cached_method
    def number_of_points(self):
        if self.gaussian is None:
            raise ValueError("No gaussian grid defined for %s" % (self.request,))
        return gaussian_number_of_values(self.gaussian, *self.area.bounding_box())

    @cached_method
    def is_global(self):
        number_of_points = self.number_of_points()
        global_points = gaussian_number_of_values(self.gaussian, 90, 0, -90, 360)
        return number_of_points == global_points

    def factor_R(self, reference):
        model_grid, model_gaussian, model_resol = reference
        LOG.debug("factor_R gaussian=%s reference=%s", self.gaussian, reference)
        return self.N / model_gaussian

    def explain_R(self, reference):
        model_grid, model_gaussian, model_resol = reference
        return f"{self.N} / {model_gaussian}"

    def reference_grid(self, reference):
        return reference[1]

    def number_of_pl(self):
        if self.gaussian.startswith("F"):  # No PL in full gaussians
            return 0
        north, west, south, east = self.adjusted_area()
        return number_of_pl(self.gaussian, north, south)

    def details(self):
        return f"grid: {self.gaussian}, area: {self.area}"


class Spectral(Field):

    name = "spectral"

    resol = None

    def set_grid(self, *args):
        return LatLon(self.request).set_grid(*args)

    def set_gaussian(self, *args):
        return Gaussian(self.request).set_gaussian(*args)

    def set_resol(self, resol):
        self.resol = resol
        return self

    def encoded_values(self):
        npoints = self.number_of_points()
        nmissing = 0
        return npoints, nmissing

    def number_of_points(self):
        assert self.resol, self.request
        T = self.resol
        return (T + 1) * (T + 2)

    def factor_A(self):
        # Always global
        return 1

    def explain_A(self):
        return "spectral fields are global"

    def factor_R(self, reference):
        assert self.resol, self.request

        model_grid, model_gaussian, model_resol = reference
        LOG.debug("factor_R resol=%s reference=%s", self.resol, reference)

        return (self.resol + 1) / (model_resol + 1)

    def explain_R(self, reference):
        model_grid, model_gaussian, model_resol = reference
        return f"({self.resol} + 1) / ({model_resol} + 1)"

    def reference_grid(self, reference):
        return reference[2]

    def number_of_pl(self):
        return 0

    def is_global(self):
        return False

    def details(self):
        return f"resol: {self.resol}"


class ReducedLL(Gridded):

    name = "reduced_ll"

    def set_grid(self, we, sn):
        return LatLon(self.request).set_grid(we, sn)

    @cached_method
    def number_of_points(self):
        return reduced_latlon_number_of_points(
            self.grid_name,
            *self.area.bounding_box(),
        )

    @cached_method
    def is_global(self):
        number_of_points = self.number_of_points()
        global_points = reduced_latlon_number_of_points(self.grid_name, 90, 0, -90, 360)
        return number_of_points == global_points

    def number_of_pl(self):
        return number_of_pl(self.grid_name, 90, -90)

    @property
    def grid_name(self):
        name = str(self.reduced_ll).replace(".", "_")
        return f"reduced-{name}"

    def factor_R(self, reference):
        grid = self.reduced_ll

        model_grid, model_gaussian, model_resol = reference
        LOG.debug("factor_R reduced_grid=%s reference=%s", grid, reference)

        return model_grid / grid

    def explain_R(self, reference):
        grid = self.reduced_ll

        model_grid, model_gaussian, model_resol = reference

        return f"{model_grid} / {grid}"

    def reference_grid(self, reference):
        return self.reduced_ll

    def wave_missing_values_ratio(self):
        return self.request.land_sea_ratio("mask_reduced")

    def details(self):
        return f"area: {self.area}"


class Mixed(Field):
    _sh = None
    _gg = None

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)
        self.kwargs = kwargs

    def set_grid(self, *args):
        return LatLon(self.request).set_grid(*args)

    def set_gaussian(self, *args):
        return Gaussian(self.request).set_gaussian(*args)

    def split(self):
        from .request import Request

        def _copy_attributes(other):
            if self.resol:
                other = other.set_resol(self.resol)
            if self.accuracy:
                other = other.set_accuracy(self.accuracy)
            return other

        if self._sh is None and self._gg is None:
            spherical_harmonics = set(config("spherical_harmonics")["param"])
            params = set(self.request.fields["param"])
            sh = params.intersection(spherical_harmonics)
            gg = params.difference(sh)

            if sh and gg:
                self._sh = _copy_attributes(
                    Spectral(Request(self.request, param=tuple(sh)), **self.kwargs)
                )
                self._gg = _copy_attributes(
                    Gaussian(Request(self.request, param=tuple(gg)), **self.kwargs)
                )
            elif sh:
                self._sh = _copy_attributes(Spectral(self.request, **self.kwargs))
            else:
                self._gg = _copy_attributes(Gaussian(self.request, **self.kwargs))

            LOG.debug("SPLIT %s", self.request)
            LOG.debug(" => SH %s", self._sh.request if self._sh else None)
            LOG.debug(" => GG %s", self._gg.request if self._gg else None)

        return self._sh, self._gg

    def set_resol(self, *args):
        sh, gg = self.split()
        if sh is not None and gg is not None:
            self._sh = self._sh.set_resol(*args)
            self._gg = self._gg.set_resol(*args)
            return self

        if sh is not None:
            return self._sh.set_resol(*args)
        else:
            return self._gg.set_resol(*args)

    def set_area(self, *args):
        sh, gg = self.split()
        if sh is not None and gg is not None:
            return super().set_area(*args)

        if sh is not None:
            return sh.set_area(*args)
        else:
            return gg.set_area(*args)

    def finalise(self):
        sh, gg = self.split()
        if sh is not None and gg is not None:
            return self

        if sh is not None:
            return sh
        else:
            return gg

    def estimated_volume(self):
        sh, gg = self.split()
        if sh is not None and gg is not None:
            return sh.estimated_volume() + gg.estimated_volume()

        if sh is not None:
            return sh.estimated_volume()
        else:
            return gg.estimated_volume()

    def factor_A(self):
        sh, gg = self.split()
        assert (sh is not None and gg is None) or (
            sh is None and gg is not None
        ), self.request
        if sh is not None:
            return sh.factor_A()
        else:
            return gg.factor_A()


class Rotation:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def __repr__(self):
        return f"{self.lat}/{self.lon}"


class Point:
    def __init__(self, lat, lon, tag):
        self.lat = lat
        self.lon = lon

    def __repr__(self):
        return f"{self.lat}/{self.lon}"


class Unknown(Repres):
    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)
        LOG.error("Cannot guess the representation of %s", request)

    def set_grid(self, we, sn):
        # We can guess that the output will be lat/lon
        return LatLon(self.request).set_grid(we, sn)

    def set_gaussian(self, *args):
        # We can guess that the output will be gaussian
        return Gaussian(self.request).set_gaussian(*args)

    def estimated_volume(self):
        raise ValueError("Cannot estimated the volume of %s", self.request)


class WP(Repres):
    name = "timeseries"
    locations = 1

    def set_location(self, n):
        self.locations = n
        return self

    def set_point(self, area):
        assert isinstance(area, Point)
        return self

    def estimated_volume(self):
        # See webdev/..../dissemination_requirements.py
        sizes = config("volumes_estimates")["weather_parameters"]

        product_count = 1
        for k, v in self.request.fields.items():
            if k not in ("step", "number"):
                product_count *= len(v)

        product_size = sizes[self.request.stream]

        return product_count * product_size

    def factor_A(self):
        return config("minimum_area") / (360 * 180)

    def _for_R(self):
        from .request import Request
        from .splitters import prepare_request

        TYPES = dict(oper="fc", enfo="cf")

        r = Request(
            self.request.fields,
            param=("2t",),
            levtype=("sfc",),
            type=(TYPES[self.request.stream],),
        )
        return prepare_request(r)

    def factor_R(self, reference):
        return self._for_R().repres.factor_R(reference)

    def explain_R(self, reference):
        return self._for_R().repres.explain_R(reference)

    def reference_grid(self, reference):
        return reference[0]

    def number_of_chargeable_items(self, request):
        params = len(request.fields["param"])
        params_rounded = 8
        steps = len(request.fields["step"])
        times = len(request.fields["time"])
        locations = self.locations
        LOG.debug(
            "WP Number of chargeable items param=%s param8=%s steps=%s times=%s locations=%s",
            params,
            params_rounded,
            steps,
            times,
            locations,
        )
        return params_rounded * steps * times * locations

    def explain_items(self, request):
        steps = len(request.fields["step"])
        times = len(request.fields["time"])
        locations = self.locations
        return (
            f"(always 8 parameters) * ({times} times) * ({steps} steps)"
            f" * ({locations} locations)"
        )

    def explain_A(self):
        minimum_area = config("minimum_area")
        return f"minimum area {minimum_area} / (360 * 180)"

    def is_global(self):
        return False

    def details(self):
        return f"locations: {self.locations}"


class TF(Repres):
    name = "track"
    area = "undefined"

    def estimated_volume(self):
        # See webdev/..../dissemination_requirements.py
        sizes = config("volumes_estimates")["cyclone_tacks"]
        product_count = len(self.request.fields["time"])
        product_size = sizes[self.request.stream]

        return product_count * product_size

    def factor_A(self):
        return 0

    def factor_R(self, reference):
        return 0

    def reference_grid(self, reference):
        return reference[0]

    def number_of_chargeable_items(self, request):
        return 0

    def explain_A(self):
        return "non-chargeable"

    def explain_R(self, reference):
        return "non-chargeable"

    def explain_items(self, request):
        return "non-chargeable"

    def set_area(self, area):
        self.area = area
        return self

    def is_global(self):
        return False

    def details(self):
        return f"area: {self.area}"

    def used_when_computing_free_data_grid(self):
        return False


REPRES = {
    ("reduced_gg", "sh"): Mixed,
    "wp": WP,
    "tf": TF,
    "reduced_gg": Gaussian,
    "sh": Spectral,
    "reduced_ll": ReducedLL,
    "regular_ll": LatLon,
    "unknown": Unknown,
}


def repres(request):

    repres = representation_matcher.get_match(request)
    type = repres["type"] if repres else "sh"
    if isinstance(type, (list, tuple)):
        type = tuple(sorted(set(type)))
        if len(type) == 1:
            type = type[0]

    repres = REPRES[type](request, **repres)

    use = request.use

    location = use.get("location")  # Only used by costing
    if location is not None:
        repres = repres.set_location(int(location[0]))

    postproc = request.postproc

    grid = postproc.get("grid")
    if grid is not None:
        assert len(grid) in [1, 2], request
        if len(grid) == 1:
            repres = repres.set_gaussian(grid[0])
        else:
            repres = repres.set_grid(
                float(grid[0]),
                float(grid[1]),
            )

    gaussian = postproc.get("gaussian")
    if gaussian is not None:
        log_warning_once(
            LOG,
            "Keyword 'gaussian' is deprecated and is ignored. Please use 'grid'. (%s)",
            request.tag,
        )
        # result = result.set_gaussian(*gaussian)

    resol = postproc.get("resol")
    if resol is not None:
        repres = repres.set_resol(*[int(r) for r in resol])

    area = postproc.get("area")
    if area is not None:
        assert len(area) in [2, 4], request
        if len(area) == 2:
            repres = repres.set_point(Point(*[float(a) for a in area], request.tag))
        else:
            repres = repres.set_area(Area(*[float(a) for a in area], request.tag))

    frame = postproc.get("frame")
    if frame is not None:
        repres = repres.set_frame(*[int(r) for r in frame])

    bitmap = postproc.get("bitmap")
    if bitmap is not None:
        repres = repres.set_bitmap(*bitmap)

    rotation = postproc.get("rotation")
    if rotation is not None:
        assert len(rotation) == 2, request
        repres = repres.set_rotation(Rotation(*[float(r) for r in rotation]))

    accuracy = postproc.get("accuracy")
    if accuracy is not None:
        assert len(accuracy) == 1, accuracy
        if accuracy[0] == "av":
            repres = repres.set_accuracy(AccuracyAV())
        else:
            repres = repres.set_accuracy(Accuracy(*[int(r) for r in accuracy]))

    return repres.finalise()
