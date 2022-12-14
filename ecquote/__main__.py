#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import argparse
import json
import logging
import os

from .cart import Cart
from .modify import preprocessor
from .resources import config
from .utils import as_resource


class Multiple(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        values = values.split(",")
        if "all" in values:
            values = self.const
        for v in values:
            if v not in self.const:
                choices = ", ".join(f"'{x}'" for x in self.const)
                parser.error(
                    f"argument {self.dest}: invalid choice: '{v}' (choose from {choices})"
                )

        setattr(args, self.dest, values)


def main():
    parser = argparse.ArgumentParser("ecquote")
    parser.add_argument(
        "-D", "--detailed", action="store_true", help="Print a detailed report"
    )

    parser.add_argument(
        "--show",
        const=(
            "all",
            "targets",
            "groups",
            "categories",
            "users",
            "types",
            "destinations",
        ),
        action=Multiple,
        default=[],
    )

    parser.add_argument(
        "--streams", action="store_true", help="List the streams found in the requests"
    )
    parser.add_argument("--samples")
    parser.add_argument("--split", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-w", "--warnings", action="store_true")
    parser.add_argument("-j", "--json", action="store_true")
    parser.add_argument("--csv", action="store_true")
    parser.add_argument("--destinations", action="store_true")

    parser.add_argument("--who-uses", metavar="REQUEST")
    parser.add_argument("--requests", action="store_true")
    parser.add_argument("--postproc", action="store_true")
    parser.add_argument("--waves", action="store_true")
    parser.add_argument("--landsea", metavar="AREA")
    parser.add_argument("--statistics", action="store_true")
    parser.add_argument("--strict-mode", action="store_true")
    parser.add_argument("--nofree", action="store_true")

    parser.add_argument("--number-of-points", action="store_true")
    parser.add_argument("--volume", action="store_true")
    parser.add_argument("--rest", action="store_true")
    parser.add_argument("--config", metavar="KEY=VALUE", action="append")
    parser.add_argument("--categories", metavar="PATH-TO-CSV-FILE")
    parser.add_argument("--disable-inheritance", action="store_true")

    parser.add_argument("--free-data", metavar="PATH-TO-DISS-FILE")
    parser.add_argument("--group-by", metavar="KEY1,KEY2,...")

    parser.add_argument("--modify", metavar="PATH-TO-MODIFY-YAML")
    parser.add_argument("--category", metavar="CATEGORY")

    parser.add_argument("--max-charge-core", type=int)
    parser.add_argument("--max-charge-high-frequency", type=int)

    parser.add_argument("-r", "--request")
    parser.add_argument("files", metavar="FILES-OR-DIRECTORIES", type=str, nargs="*")
    ARGS = parser.parse_args()

    level = logging.ERROR
    if ARGS.warnings:
        level = logging.WARNING
    if ARGS.verbose:
        level = logging.INFO
    if ARGS.debug:
        level = logging.DEBUG

    # logging.basicConfig(
    #     format="%(asctime)s %(levelname)-8s %(message)s",
    #     level=level,
    #     datefmt="%Y-%m-%d %H:%M:%S",
    # )

    logging.basicConfig(
        format="%(levelname)-8s %(message)s",
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if ARGS.nofree:
        config("free-open-data", False)
        config("free-wmo-essential", False)

    if ARGS.free_data:
        config("free-data", os.path.realpath(ARGS.free_data))

    if ARGS.group_by:
        config("group-by", ARGS.group_by)

    if ARGS.modify:
        config("modify", ARGS.modify)

    if ARGS.config:
        for c in ARGS.config:
            k, v = c.split("=")
            config(k, as_resource(v))

    if ARGS.category:
        if not ARGS.categories:
            parser.error("Please provide a CSV files of categories")
        config("category", ARGS.category)

    if ARGS.categories:
        config("categories", ARGS.categories)

    if ARGS.strict_mode:
        config("strict-mode", True)

    if ARGS.destinations:
        config("destinations", True)

    if ARGS.max_charge_core is not None:
        config("max-charge-core", ARGS.max_charge_core)

    if ARGS.max_charge_high_frequency is not None:
        config("max-charge-high-frequency", ARGS.max_charge_high_frequency)

    if ARGS.rest:
        from ecquote.rest import run

        run(ARGS)
        exit(0)

    if ARGS.landsea:
        from .landsea import land_sea_ratio

        args = [as_resource(x) for x in ARGS.landsea.split("/")]
        print(land_sea_ratio(*args))
        exit(0)

    if ARGS.request:
        make_cart = Cart.from_strings
        make_cart_arg = ARGS.request
    else:
        if not ARGS.files:
            parser.error("Please provide at least one file or directory.")
        make_cart = Cart.from_request_files
        make_cart_arg = ARGS.files

    cart = make_cart(
        make_cart_arg,
        inherit=not ARGS.disable_inheritance,
        preprocessor=preprocessor(ARGS.modify),
        categories=ARGS.categories,
        category=ARGS.category,
    )

    if ARGS.postproc:
        cart.postproc(ARGS.waves)
        exit(0)

    if ARGS.streams:
        cart.streams()
        exit(0)

    if ARGS.waves:
        cart.waves()
        exit(0)

    if ARGS.samples:
        cart.samples(ARGS.samples)
        exit(0)

    if ARGS.split:
        cart.split(ARGS.split)
        exit(0)

    if ARGS.who_uses:
        cart.who_uses(ARGS.who_uses)
        exit(0)

    if ARGS.requests:
        cart.dump_requests()
        exit(0)

    if ARGS.statistics:
        cart.statistics()
        exit(0)

    if ARGS.number_of_points:
        print(cart.requests[0].repres.number_of_points())
        exit(0)

    if ARGS.volume:
        print(cart.requests[0].estimated_volume())
        exit(0)

    if ARGS.json:
        print(
            json.dumps(
                cart.costing(),
                indent=4,
            )
        )
        return

    if ARGS.csv:
        extra = {k: True for k in ARGS.show if k != "all"}
        cart.csv(**extra)
        return

    extra = {k: True for k in ARGS.show if k != "all"}
    cart.summary(detailed=ARGS.detailed, **extra)


if __name__ == "__main__":
    main()
