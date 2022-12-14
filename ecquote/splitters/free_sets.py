#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging

from ..request import Request
from ..resources import resource_path

LOG = logging.getLogger(__name__)


def split_paid_free_set_request(
    request,
    rules,
    all_free,
    paid_requests,
    free_requests,
    depth,
    *keys,
):

    if len(keys) == 0:
        LOG.debug(
            "%ssplit_paid_free_set_request (%s) all_free=%s request=%s",
            " " * depth,
            all_free,
            all_free,
            Request(request).summary(),
        )
        if all_free:
            free_requests.append(request)
        else:
            paid_requests.append(request)
        return

    key = keys[0]

    request_values = set(request[key])
    matching = True
    rule_values = set()
    matching_rules = []

    for i, rule in enumerate(rules):
        values = set(rule[key])

        if request_values != values:
            matching = False
        else:
            matching_rules.append(rule)

        rule_values.update(values)

    if LOG.isEnabledFor(logging.DEBUG):

        LOG.debug(
            "%ssplit_paid_free_set_request (%s) request=%s",
            " " * depth,
            all_free,
            Request(request).summary(),
        )
        for i, r in enumerate(rules):
            LOG.debug(
                "%ssplit_paid_free_set_request (%s) rule %s: %s",
                " " * depth,
                all_free,
                i,
                Request(r).summary(),
            )
        LOG.debug(
            "%ssplit_paid_free_set_request (%s) matching=%s %s rule_values=%s",
            " " * depth,
            all_free,
            matching,
            key,
            rule_values,
        )

    # All matching move on...
    if matching:
        LOG.debug(
            "%ssplit_paid_free_set_request (%s) move on %s", " " * depth, all_free, key
        )
        split_paid_free_set_request(
            request,
            rules,
            all_free,
            paid_requests,
            free_requests,
            depth + 3,
            *keys[1:],
        )
        return

    paid_values = request_values.difference(rule_values)
    free_values = request_values.intersection(rule_values)

    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(
            "%ssplit_paid_free_set_request (%s) paid_values %s",
            " " * depth,
            all_free,
            paid_values,
        )
        LOG.debug(
            "%ssplit_paid_free_set_request (%s) free_values %s",
            " " * depth,
            all_free,
            free_values,
        )

        for i, r in enumerate(matching_rules):
            LOG.debug(
                "%ssplit_paid_free_set_request (%s) matching rule %s: %s",
                " " * depth,
                all_free,
                i,
                free_values,
            )

    if paid_values:
        paid_request = dict(**request)
        paid_request[key] = tuple(paid_values)
        split_paid_free_set_request(
            paid_request,
            [r for r in rules if set(r[key]).intersection(paid_values)],
            False,
            paid_requests,
            free_requests,
            depth + 3,
            *keys[1:],
        )

    if free_values:
        free_request = dict(**request)
        free_request[key] = tuple(free_values)
        split_paid_free_set_request(
            free_request,
            [r for r in rules if set(r[key]).intersection(free_values)],
            all_free,
            paid_requests,
            free_requests,
            depth + 3,
            *keys[1:],
        )


class PreserveUserValuesOrder:
    def __init__(self, values):
        self.order = {}
        for i, v in enumerate(values):
            self.order.setdefault(v, i)

    def __call__(self, x):
        return self.order[x]


class PreserveUserDictOrder:
    def __init__(self, dict):
        self.order = {}
        for i, v in enumerate(dict.keys()):
            self.order.setdefault(v, i)

    def __call__(self, x):
        return self.order[x[0]]


def _add_non_field(request, requests, free_set_name=None):

    sorter = PreserveUserDictOrder(request.fields)
    for r in requests:
        s = {}
        for k, v in sorted(r.items(), key=sorter):
            s[k] = tuple(sorted(v, key=PreserveUserValuesOrder(request.fields[k])))
        request.copy_non_fields_values(s)
        r = Request(request, s)
        if free_set_name is not None:
            assert free_set_name != r.subset.name
            r = r.annotate("free", free_set_name, override="append")
        yield r


KEYS = (
    "class",
    "type",
    "stream",
    "dataset",
    "expver",
    "levtype",
    "domain",
    "system",
    "method",
    "origin",
    "time",
    "step",
    "fcmonth",
    "leg",
    "param",
    "levelist",
    "number",
    "frequency",
    "direction",
    "quantile",
)
KEY_ORDER = {k: i for i, k in enumerate(KEYS)}


def split_paid_free_set(request, free_set, free_set_name, ignore=[]):
    if free_set is None:
        return [request], []

    ignore = set(ignore)
    all_keys = set(request.fields.keys()) - ignore

    LOG.debug("%s all_keys %s %s", free_set_name, sorted(all_keys), ignore)

    # def _check(r):
    #     for k, v in r.items():
    #         assert v != ("off",)

    # _check(request.fields)
    rules = []
    for r in free_set:

        # _check(r.fields)
        if set(r.fields.keys()) - ignore != all_keys:
            LOG.debug(
                "%s fields %s", free_set_name, sorted(set(r.fields.keys()) - ignore)
            )
            continue

        rules.append(r.fields)

    if not rules:
        LOG.debug("%s no rules", free_set_name)
        return [request], []

    paid = []
    free = []
    split_paid_free_set_request(
        request.fields,
        rules,
        True,
        paid,
        free,
        0,
        *sorted(all_keys, key=lambda x: KEY_ORDER.get(x, 99)),
    )

    if not free:
        [request], []

    if True:
        assert request.number_of_fields() == sum(
            Request(p).number_of_fields() for p in paid
        ) + sum(Request(f).number_of_fields() for f in free), (
            request.number_of_fields(),
            sum(Request(p).number_of_fields() for p in paid),
            sum(Request(f).number_of_fields() for f in free),
        )

    paid = list(_add_non_field(request, paid))
    free = list(_add_non_field(request, free, free_set_name))

    return paid, free


GRID_AREA = set(["grid", "area"])


def coarser(g1, g2):
    return g1[0] >= g2[0] and g1[1] >= g2[1]


def match(r, free_grid):

    grid = r.postproc.get("grid")
    if grid is None or len(grid) != 2:
        return False

    if not coarser(tuple(float(x) for x in grid), free_grid) and r.type not in (
        "tf",
        "wp",
    ):
        return False

    # if not r.repres.is_global():
    #     return False

    # # Extra prosprocessing
    # if set(r.postproc.keys()) - GRID_AREA:
    #     return False

    return True


def splitter(requests, free_set_name):

    from ..cart import Cart

    debug = LOG.isEnabledFor(logging.DEBUG)

    path = (
        free_set_name if free_set_name.startswith("/") else resource_path(free_set_name)
    )

    free_cart = Cart.from_request_files(
        path,
        inherit=True,
    )

    free_grid = set()
    for r in free_cart.requests:
        if r.repres.used_when_computing_free_data_grid():
            try:
                free_grid.add(r.repres.grid)
            except AttributeError:
                LOG.error("%s: could not get grid from request %s", free_set_name, r)
                raise

    if len(free_grid) == 0:
        raise ValueError("Cannot establish reference grid from %s", free_set_name)

    if len(free_grid) > 1:
        raise ValueError("Too many gris in %s: %s", free_set_name, free_grid)

    free_grid = list(free_grid)[0]
    free_grid = tuple(float(x) for x in free_grid)
    # free_postproc = dict(grid=free_grid)

    public_sets = free_cart.by_product_sets
    if debug:
        for k in public_sets.keys():
            LOG.debug("%s: public_sets %s", free_grid, k)

    for r in requests:

        LOG.debug("%s: postproc %s and %s", free_set_name, free_grid, r.postproc)

        if not match(r, free_grid):
            LOG.debug("%s: grids do not match", free_set_name)
            yield r
            continue

        LOG.debug("%s: grids match", free_set_name)
        free_set = public_sets.get(r.subset)
        if free_set is None:
            LOG.debug("%s: no subset %s in free set", free_set_name, r.subset)
            yield r
            continue

        paid, free = split_paid_free_set(r, free_set, free_set_name, [])
        LOG.debug("%s: paid %s", free_set_name, paid)
        LOG.debug("%s: free %s", free_set_name, free)

        yield from (
            x.annotate("split", free_set_name, override="append", only_if=free)
            for x in paid
        )
        yield from (
            x.annotate("split", free_set_name, override="append", only_if=paid)
            for x in free
        )
