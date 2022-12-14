#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import datetime
import logging
from collections import defaultdict

from .landsea import land_sea_ratio
from .matching import Matcher
from .repres import repres
from .resources import config, resource
from .utils import cached_method, log_warning_once, plural

LOG = logging.getLogger(__name__)

wave_streams = set(config("wave_streams"))
ml_matcher = Matcher("representations", lambda _, model_levels, **kwargs: model_levels)


# Not in MARS or not pgen/mars language mismatch

RENAME = {
    "gh": "z",
    "gha": "za",
}


def paramid(name):
    name = RENAME.get(name, name)
    mapping = resource("params")
    return mapping.get(name, name)


def to_by(d):

    for k in ("step", "levelist", "number"):
        if k in d and len(d[k]) > 5:
            ok = True
            try:
                diff = int(d[k][1]) - int(d[k][0])
                for i, s in enumerate(d[k][2:]):
                    if int(d[k][i + 2]) - int(d[k][i + 1]) != diff:
                        ok = False
                        break
            except ValueError:
                ok = False
            if ok:
                if diff == 1 and k not in ("step",):
                    d[k] = tuple([d[k][0], "to", d[k][-1]])
                else:
                    d[k] = tuple([d[k][0], "to", d[k][-1], "by", str(diff)])


KEYWORDS = None
ORDER = {}


def reversed_keywords_mapping():
    global KEYWORDS
    if KEYWORDS is None:
        KEYWORDS = {}
        for i, (group, params) in enumerate(config("keywords").items()):
            ORDER[group] = i
            for p in params:
                KEYWORDS[p] = group
    return KEYWORDS


class RequestList(list):
    def append(self, *args, **kwargs):
        raise ValueError("Cannot modify a RequestList")

    def __setitem__(self, key, value):
        raise ValueError("Cannot modify a RequestList")


class Request:
    def __init__(self, *args, attributes=None, **kwargs):
        from .parser import parse_single_request

        self._groups = defaultdict(dict)

        w = set()
        attrs = {}
        dates = None
        r = {}
        for a in args:
            if isinstance(a, Request):
                w.update(a._warnings)
                attrs.update(a._attributes)
                dates = a._dates
                a = a.as_dict()
            if isinstance(a, str):
                a = parse_single_request(a)
            r.update(a)
        r.update(kwargs)

        keyword_to_group = reversed_keywords_mapping()

        for k, v in r.items():
            assert isinstance(v, tuple), (k, v)
            v = tuple(str(x) for x in v)
            if len(v) == 1 and v[0] in ("off",):
                continue

            self._groups[keyword_to_group[k]][k] = v

        self._dates = dates
        if "ignore" in self._groups and "date" in self._groups["ignore"]:
            self._dates = len(self._groups["ignore"]["date"])

        if "attributes" in self._groups:
            attrs.update(self._groups["attributes"])
            self._groups.pop("attributes", None)

        self._groups.pop("ignore", None)
        self._warnings = w

        if attributes is not None:
            attrs.update(attributes)
        self._attributes = attrs

        # Just in case
        if self.fields.get("stream", (None,))[0] in wave_streams:
            self.fields["levtype"] = ("sfc",)

        # for k,v in list(self._groups.items()):
        #     self._groups[k] = FrozenDict(v)

    @classmethod
    def from_dict(cls, d):
        "To use when the dict is not made of tuples"
        r = {}
        for k, v in d.items():
            if isinstance(v, (list, tuple)):
                r[k] = tuple(str(x) for x in v)
            else:
                r[k] = (str(v),)
        return cls(r)

    def __repr__(self):
        try:
            result = []
            for _, r in sorted(self._groups.items(), key=lambda x: ORDER[x[0]]):
                for k, v in r.items():
                    result.append(f"{k}={'/'.join(v)}")
            return ",".join(result)
        except TypeError:
            for _, r in sorted(self._groups.items(), key=lambda x: ORDER[x[0]]):
                for k, v in r.items():
                    print(k, v)
            raise

    def as_dict(self):
        result = {}
        for g in self._groups.values():
            result.update(g)
        return result

    @cached_method
    def frequency(self):
        use = tuple(sorted(self.use.get("use", [])))

        def default():
            return self.subset.frequency

        def daily():
            # assert self.subset.frequency == 365, (self.subset, self.subset.frequency)

            if self.subset.frequency != 365:
                log_warning_once(
                    LOG,
                    "Expecting frequency 365 for subset %s, got %s (%s)",
                    self.subset.name,
                    self.subset.frequency,
                    self,
                )

            return self.subset.frequency

        def weekly():
            if self.subset.frequency != 104:
                log_warning_once(
                    LOG,
                    "Keyword use=%s is ignored for subset %s %s (%s)",
                    "/".join(use),
                    self.subset.name,
                    self.subset.frequency,
                    self,
                )
                return self.subset.frequency
            return 52

        def byweekly():
            if self.subset.frequency != 104:
                log_warning_once(
                    LOG,
                    "Keyword use=%s is ignored for subset %s %s (%s)",
                    "/".join(use),
                    self.subset.name,
                    self.subset.frequency,
                    self,
                )
                return self.subset.frequency
            return 104

        def monthly():
            # Here so we can test legacy requests
            log_warning_once(
                LOG,
                "Keyword use=monthly is ignored for subset %s (%s)",
                self.subset.name,
                self,
            )
            return self.subset.frequency

        return {
            tuple(): default,
            ("bc",): daily,
            ("monday", "thursday"): byweekly,
            ("monday",): weekly,
            ("thursday",): weekly,
            ("monthly",): monthly,
        }[use]()

    @cached_method
    def number_of_fields(self):
        debug = LOG.isEnabledFor(logging.DEBUG)
        count = 1
        counts = {}
        for k, v in self.fields.items():
            assert isinstance(v, (list, tuple)), v
            if debug:
                counts[k] = len(v)
            count *= len(v)

        if self.is_hindcast():
            count *= config("hindcast_dates")

        if debug:
            if self.is_hindcast():
                LOG.debug(
                    "number_of_fields (hindcast dates=%s) %s %s",
                    config("hindcast_dates"),
                    count,
                    counts,
                )
            else:
                LOG.debug("number_of_fields %s %s", count, counts)
        return count

    def explain_fields(self):

        bits = []
        nice = dict(levelist="level")

        for k, v in self.fields.items():
            if len(v) > 1:
                p = plural(len(v), nice.get(k, k))
                bits.append(f"({p})")

        if self.is_hindcast():
            bits.append(f'({config("hindcast_dates")} hindcast dates)')

        if bits:
            return " * ".join(bits)
        else:
            return "1 field"

    @cached_method
    def number_of_chargeable_items(self):
        return self.repres.number_of_chargeable_items(self)

    def explain_items(self):
        return self.repres.explain_items(self)

    def land_sea_ratio(self, method=None):
        return land_sea_ratio(
            *self.repres.area.bounding_box(),
            method=method,
        )

    @cached_method
    def estimated_volume(self):
        return self.repres.estimated_volume()

    @property
    @cached_method
    def repres(self):
        return repres(self)

    @property
    @cached_method
    def type(self):
        assert len(self.fields["type"]) == 1
        return self.fields["type"][0]

    @property
    @cached_method
    def stream(self):
        assert len(self.fields["stream"]) == 1
        return self.fields["stream"][0]

    @property
    @cached_method
    def levtype(self):
        if "levtype" not in self.fields:
            LOG.debug("Request with no levtype: %s", self)
            return None
        assert len(self.fields["levtype"]) == 1, self
        return self.fields["levtype"][0]

    @property
    @cached_method
    def tag(self):
        if "target" not in self.disposition:
            return "---:--"
        assert len(self.disposition["target"]) == 1
        return self.disposition["target"][0]

    @property
    @cached_method
    def params(self):
        return self.fields["param"]

    @property
    @cached_method
    def fields(self):
        return self._groups["fields"]

    @property
    @cached_method
    def postproc(self):
        return self._groups["postproc"]

    @property
    @cached_method
    def disposition(self):
        return self._groups["disposition"]

    @property
    @cached_method
    def use(self):
        return self._groups.get("use", {})

    def copy_non_fields_values(self, s):
        for g, r in self._groups.items():
            if g == "fields":
                continue
            s.update(r)

    def sample_mars_request(self):
        date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        date = date.date()

        r = {k: v[0] for k, v in self.fields.items()}
        r.update(self.use)
        r.setdefault("levtype", "off")

        if (r["stream"], r["type"], r["levtype"]) in (
            ("scda", "an", "pv"),
            ("scda", "an", "pt"),
        ):
            # Not in MARS
            r["stream"] = "oper"

        if (r["stream"], r["type"], r["levtype"]) in (("enfo", "cs", "pl"),):
            pass
        elif (r["stream"], r["type"], r["levtype"]) in (
            ("enfo", "cf", "ml"),
            ("enfo", "pf", "ml"),
            ("efov", "cf", "ml"),
            ("efov", "pf", "ml"),
        ):
            # Not in MARS
            r["param"] = "q/z"
        else:
            # Not all param avalailable at all levels
            if r["levtype"] not in ("sfc", "off"):
                if r["type"] not in ("an", "fc", "cf", "pf"):
                    r["levelist"] = "all"
                r["param"] = "all"

        if r.get("use") == "bc":
            del r["use"]

        if r.get("use") in ("monday", "thursday", "monthly") or r.get("stream") in (
            "efov",
            "efhs",
            "enfh",
            "enwh",
        ):
            while date.weekday() not in (0, 3):
                date = date - datetime.timedelta(days=1)
            r.pop("use", None)

        if r.get("system"):
            # Seasonal run on the first
            date = datetime.date(date.year, date.month, 1)

        r.pop("leg", None)
        assert "use" not in r, r["use"]

        if r["stream"] in ("enfh", "enwh"):  # TODO: add to config
            hdate = datetime.date(date.year - 5, date.month, date.day)
            r["hdate"] = hdate.isoformat()
            r["levtype"] = "sfc"

        if "step" in self.subset.mars:
            r["step"] = "/".join(set(str(x) for x in self.subset.mars["step"]))
            r["time"] = "0/12"
            r["expect"] = "any"

        if "param" in self.subset.mars:
            r["param"] = "/".join(self.subset.mars["param"])
            r["expect"] = "any"

        if "param" in r:
            r["param"] = "/".join(set(str(paramid(x)) for x in r["param"].split("/")))

        # Just in case
        r["frequency"] = r["direction"] = 1
        r["date"] = date.isoformat()
        return ",".join(f"{k}={v}" for k, v in r.items())

    def factor_B(self):
        return 0 if self._attributes.get("free") else 20

    def factor_A(self):
        return self.repres.factor_A()

    def factor_R(self, reference):
        return self.repres.factor_R(reference(self))

    def explain_A(self):
        return self.repres.explain_A()

    def explain_R(self, reference):
        return self.repres.explain_R(reference(self))

    def reference_grid(self, reference):
        return self.repres.reference_grid(reference(self))

    def number_of_pl(self):
        return self.repres.number_of_pl()

    def number_of_model_levels(self):
        try:
            return ml_matcher.get_match(self)
        except Exception:
            print(self)
            raise

    def dates(self):
        return self._dates

    def summary(self):
        d = self.as_dict()
        for k in (
            "class",
            "expver",
            "domain",
            "target",
            "option",
            "priority",
        ):
            d.pop(k, None)

        to_by(d)

        for k, v in list(d.items()):
            if len(v) > 5:
                d[k] = tuple(list(v[:2]) + ["..."] + list(v[-2:]))

        if "time" in d:
            d["time"] = tuple(t[:2] for t in d["time"])

        return repr(Request(d))

    def add_warning(self, msg):
        self._warnings.add(msg)

    def warnings(self):
        return self._warnings

    def is_wave(self):
        return self.stream in config("wave_streams")

    def is_hindcast(self):
        return self.stream in config("hindcast_streams")

    def is_seasonal(self):
        return self.stream in config("seasonal_streams")

    def annotate(self, name, value, override=None, only_if=True):
        if not only_if:
            return self
        if override is None:
            assert name not in self._attributes, (name, value, self._attributes[name])
        if override:
            if override == "append" and name in self._attributes:
                if not isinstance(self._attributes[name], list):
                    self._attributes[name] = [self._attributes[name]]
                self._attributes[name].append(value)
            else:
                self._attributes[name] = value
        else:
            self._attributes.setdefault(name, value)
        return self

    @property
    def subset(self):
        return self._attributes["subset"]

    @property
    def free(self):
        return self._attributes.get("free")

    @property
    def lineno(self):
        if "line" in self._attributes:
            return "{}:{}".format(
                self._attributes["path"][0], self._attributes["line"][0]
            )

    @property
    def group(self):
        return self._attributes.get("group", "core")

    @property
    def category(self):
        return self._attributes.get("category")

    @property
    def user(self):
        return self._attributes.get("user")

    @property
    def destination(self):
        return self._attributes.get("destination")

    def dump(self, all_keys=None, **kwargs):
        if all_keys is None:
            all_keys = set()
        all_keys.update(self.as_dict().keys())

        s = self.as_dict()

        for k in all_keys:
            s.setdefault(k, ("off",))

        to_by(s)

        t = []
        for k, v in s.items():

            if k in ("leg", "dataset"):
                continue

            v = "/".join(str(x) for x in v)
            t.append(f"{k}={v}")
        print(",\n".join(t), **kwargs)
        print(**kwargs)

    def __eq__(self, other):
        return self._groups == other._groups

    def __hash__(self):
        h = tuple((k, hash(tuple(v.items()))) for k, v in self._groups.items())
        return hash(h)

    def full_dump(self):
        return f"{self._groups} @ {self._attributes}"
