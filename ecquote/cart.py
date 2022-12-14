#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import itertools
import logging
import os
from collections import defaultdict

from .costing import costing
from .parser import parse_request_file, parse_request_string
from .request import Request, RequestList
from .resources import config
from .splitters import first_splitters, second_splitters
from .utils import as_dict, as_numbers, cached_method, iterate_request, progress

LOG = logging.getLogger(__name__)


def identity(x):
    return x


class Cart:
    def __init__(self, requests, preprocessor=None, **kwargs):

        self._kwargs = kwargs

        if preprocessor is None:
            preprocessor = identity

        self.requests = RequestList(
            first_splitters(
                (Request(preprocessor(r)) for r in requests),
                **kwargs,
            )
        )

        by_product_sets = defaultdict(list)
        for r in self.requests:
            by_product_sets[r.subset].append(r)
        self.by_product_sets = {k: RequestList(v) for k, v in by_product_sets.items()}

        self._second_splitters = False

    @classmethod
    def from_request_files(cls, *args, inherit=False, preprocessor=None, **kwargs):
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            args = args[0]

        requests = []
        for path in args:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.endswith(".req"):
                            full = os.path.join(root, file)
                            requests += parse_request_file(full, inherit)
            else:
                requests += parse_request_file(path, inherit)

        return cls(requests, preprocessor, **kwargs)

    @classmethod
    def from_strings(cls, *args, inherit=False, **kwargs):
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            args = args[0]
        requests = []
        for s in args:
            requests += parse_request_string(s, inherit)
        return cls(requests, **kwargs)

    @classmethod
    def from_json(cls, msg, **kwargs):
        assert isinstance(msg, (list, dict))
        if isinstance(msg, list):
            requests = msg
        else:
            requests = msg["requests"]

        return cls(requests, **kwargs)

    @property
    def product_sets(self):
        return list(self.by_product_sets.keys())

    @cached_method
    def _costing(self):

        if not self._second_splitters:
            self.requests = RequestList(second_splitters(self.requests, **self._kwargs))
            self._second_splitters = True

        return costing(self.requests)

    def costing(self):
        return as_dict(self._costing())

    def csv(self, **kwargs):
        self._costing().csv(**kwargs)

    def summary(
        self,
        **kwargs,
    ):
        self._costing().summary(**kwargs)

    def postproc(self, waves=False):
        seen = set()
        for r in self.requests:
            if r.type in ("tf", "wp"):
                continue
            result = []
            for k, v in sorted(r.postproc.items()):
                if k in ("compatibility", "packing"):
                    continue
                result.append(f"{k}={'/'.join(v)}")
            if waves:
                s = "wave" if r.is_wave() else "oper"
                result.append(f"stream={s}")
            result = ",".join(result)
            if result not in seen:
                print(result)
                seen.add(result)

    def waves(self):
        wave_streams = config("wave_streams")
        seen = set()
        for r in self.requests:
            if r.type in ("tf", "wp"):
                continue
            if r.stream not in wave_streams:
                continue
            result = []
            for k, v in sorted(r.postproc.items()):
                if k not in ("area,"):
                    continue
                result.append(f"{k}={'/'.join(v)}")
            result = ",".join(result)
            if result not in seen:
                print(result)
                seen.add(result)

    def streams(self):
        seen = set()
        for r in self.requests:
            result = r.stream
            if result not in seen:
                print(result)
                seen.add(result)

    def samples(self, keywords):
        keywords = keywords.split(",")

        seen = set()
        for r in self.requests:
            result = "-".join(r.fields.get(k, ["off"])[0] for k in keywords)
            if result not in seen:
                print(
                    result,
                    r.sample_mars_request(),
                )
                seen.add(result)

    def who_uses(self, request):
        def r2dict(r):
            r = r.as_dict()
            for k in ("area", "grid", "rotation"):
                if k in r:
                    r[k] = (r[k],)
            return as_numbers(r)

        request = r2dict(Request(request.lower()))
        fields = [
            dict(zip(request.keys(), x)) for x in itertools.product(*request.values())
        ]

        seen = set()
        for r in self.requests:

            for f in fields:
                cnt = 0
                for k, v in f.items():
                    if v in r2dict(r).get(k, []):
                        cnt += 1
                if cnt == len(f):
                    seen.add(r.tag)
                    print(r.tag, r)

    def dump_requests(self, **kwargs):
        all_keys = set()
        for r in self.requests:
            r.dump(all_keys, **kwargs)
            print(**kwargs)  # An extra line for the perl

    def frequency(self):
        f = list(set(r.frequency() for r in self.requests))
        # assert len(f) == 1, f
        return min(f)

    def dates(self):
        f = list(set(r.dates() for r in self.requests))
        assert len(f) == 1, f
        assert f[0] is not None, [r._groups for r in self.requests]
        return f[0]

    def statistics(self):

        count = defaultdict(int)
        names = ("param", "step", "levelist", "stream", "type")
        for r in progress(self.requests):
            if r.type == "wp":
                continue
            for x in iterate_request({k: v for k, v in r.fields.items() if k in names}):
                k = tuple(x.get(n, "-") for n in names)
                count[k] += 1

        print(",".join(list(names) + ["count"]))
        for i, (k, v) in enumerate(
            sorted(count.items(), key=lambda x: x[1], reverse=True)
        ):
            print(",".join(list(k) + [str(v)]))
