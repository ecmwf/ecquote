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
import sys
from collections import defaultdict

from . import __version__
from .resources import config
from .resources import resource
from .utils import bytes
from .utils import capture_warnings
from .utils import log_warning_once
from .utils import plural
from .utils import progress
from .utils import roman

LOG = logging.getLogger(__name__)

"""
https://www.ecmwf.int/en/forecasts/accessing-forecasts/payment-rules-and-options/tariffs-examples
ECMWF/ACDP/5(04)6)
ECMWF/ACDP/8(07)A introduces M


"""


def band(volume):
    daily_gb = volume / 365 / 1024 / 1024 / 1024
    volume_bands = resource("volume-bands")

    for gb, price in sorted(volume_bands.items()):
        if daily_gb <= gb:
            return gb, price["euros"], None, daily_gb

    return None, None, f"Daily volume exceeds {max(volume_bands.keys())}", daily_gb


def data_values_band(data_values):
    daily_data_values_millions = data_values / 365 / 1000 / 1000
    data_values_band = resource("data-values-bands")

    for million, price in sorted(data_values_band.items()):
        if daily_data_values_millions <= million:
            return million, price["euros"], None, daily_data_values_millions

    return (
        None,
        None,
        f"Daily data values exceeds {max(data_values_band.keys())}",
        daily_data_values_millions,
    )


def commercial(s):
    s = s.lower()
    return ("commercial" in s) and ("non-commercial" not in s)


class Roman:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return self.n

    @property
    def order(self):
        return roman(self.n)

    def __lt__(self, other):
        return self.order < other.order

    def __eq__(self, other):
        return self.n == other.n

    def __hash__(self):
        return hash(self.n)


class Coster:
    def __init__(self):
        self.yearly_volume = 0
        self.yearly_fields = 0
        self.yearly_data_values = 0
        self.daily_volume = 0
        self.daily_fields = 0
        self.daily_data_values = 0
        self.requests = []
        self.subcosts = {}
        self.experimental = config("experimental")

    def add(self, *requests):
        for r in progress(requests, "Volumes"):
            with capture_warnings(r):
                self.yearly_volume += r.estimated_volume() * r.frequency()
                self.yearly_fields += r.number_of_fields() * r.frequency()
                self.daily_volume += r.estimated_volume()
                self.daily_fields += r.number_of_fields()
                if self.experimental:
                    self.yearly_data_values += r.data_values() * r.frequency()
                    self.daily_data_values += r.data_values()
        self.requests += requests

    def as_dict(self):
        result = {
            "yearly_volume": self.yearly_volume,
            "yearly_fields": self.yearly_fields,
            "worst_daily_volume": self.daily_volume,
            "worst_daily_fields": self.daily_fields,
            "average_daily_volume": int(self.yearly_volume / 365 + 0.5),
            "average_daily_fields": int(self.yearly_fields / 365 + 0.5),
        }

        band, euro, error, ref = self.band()
        if error:
            result["volume_band"] = error
        else:
            result["volume_band"] = band
            result["volume_cost"] = euro

        if self.experimental:
            result["yearly_data_values"] = self.yearly_data_values
            result["average_daily_data_values"] = int(self.yearly_data_values / 365 + 0.5)

            band, euro, error, ref = self.data_values_band()

            if error:
                result["data_values_band"] = error
            else:
                result["data_values_band"] = band
                result["data_values_cost"] = euro

            try:
                result["diff"] = result["data_values_cost"] - result["volume_cost"]
            except KeyError:
                result["diff"] = None

            result["data_values_ref"] = ref
            result["data_values_ratio"] = self.yearly_volume / self.yearly_data_values

        return result

    def summary(self, title):
        print(title)
        print()
        print("   Yearly volume:   ", bytes(self.yearly_volume))
        print("   Yearly fields:   ", "{:,}".format(self.yearly_fields))

        band, euro, error, _ = self.band()
        if error:
            print("   Volume band:     ", error)
        else:
            print("   Volume band:     ", bytes(band * 1024 * 1024 * 1024))
            print("   Volume cost:     ", "EUR {:,}".format(euro))

        if self.experimental:
            print("   Yearly values:   ", "{:,}".format(self.yearly_data_values))

            band, euro, error, _ = self.data_values_band()

            if error:
                print("   Values band:     ", error)
            else:
                print("   Values band:     ", "{:,}".format(band))
                print("   Values cost:     ", "EUR {:,}".format(euro))

            print(
                "   Values ratio:    ",
                "{:.2f}".format(self.yearly_volume / self.yearly_data_values),
            )

    def band(self):
        return band(self.yearly_volume)

    def data_values_band(self):
        return data_values_band(self.yearly_data_values)


class EPUBased(Coster):
    def __init__(self):
        super().__init__()
        self._factors = resource(self.name)
        self.epus = 0
        self.items = 0

    def add(self, *requests):
        super().add(*requests)
        for r in progress(requests, "Costing"):
            D, E, M = self.factors(r)
            self.epus += self.compute_epus(r, D, E, M)
            self.items += r.number_of_chargeable_items()

    def factors(self, request):
        subset = request.subset
        subset_name = subset.name
        if subset_name not in self._factors:
            if not request.free:
                log_warning_once(
                    LOG,
                    "Attempting to cost a free request %s with no associated paid request. (%s)",
                    subset,
                    request,
                    raise_if_strict_mode=True,
                )
            free_with = subset.free_with
            if not isinstance(free_with, (list, tuple)):
                free_with = [free_with]
            if len(free_with) > 1:
                log_warning_once(
                    LOG,
                    "Free subset %s is associated with more than one set %s.",
                    subset,
                    free_with,
                    raise_if_strict_mode=True,
                )
            log_warning_once(
                LOG,
                "%s using factors of associated subset %s.",
                subset,
                free_with[0],
            )
            subset_name = free_with[0]

        f = self._factors[subset_name]
        return f["D"], f["E"], f["M"]

    @property
    def discounted_epus(self):
        N = self.epus

        if N <= 2000:
            return N

        if N <= 20000:
            return 2000 + 0.6 * (N - 2000)

        if N <= 200000:
            return 12800 + 0.4 * (N - 20000)

        return 84800 + 0.2 * (N - 200000)

    @property
    def euros(self):
        P = config("epu-price")
        return P * self.discounted_epus

    def as_dict(self):
        result = super().as_dict()
        result["epus"] = int(self.epus)
        result["euros"] = int(self.euros)
        result["items"] = self.items
        result["discounted_epus"] = int(self.discounted_epus)

        if self.subcosts:
            result["sub_costs"] = self.subcosts

        return result

    def summary(self, title, max_charge_limit=None):
        super().summary(title)
        print("   EPUs:            ", "{:,}".format(int(self.epus)))
        print("   Discounted EPUs: ", "{:,}".format(int(self.discounted_epus)))
        print("   Information cost:", "EUR {:,}".format(int(self.euros)), end="")
        if self.subcosts:
            result = []
            for k, v in sorted(self.subcosts.items()):
                result.append("{}: {:,}".format(k, v))
            result = "; ".join(result)
            print(f" ({result})")
        else:
            print()
        if max_charge_limit is not None:
            max_charge_order = self.euros >= max_charge_limit
            print(f"   Max charge limit: EUR {max_charge_limit:,}")
            print(f"   Max charge order: {'yes' if max_charge_order else 'no'}")
        print()

    def update_subcosts(self, costs):
        total = 0
        for name, cost in costs.items():
            if self.epus:
                ratio = int(cost.epus / self.epus * self.euros)
                self.subcosts[name] = ratio
                total += ratio
            else:
                self.subcosts[name] = 0

        euros = int(self.euros)
        assert euros >= total
        for name, cost in sorted(costs.items()):
            extra = min(1, euros - total)
            self.subcosts[name] += extra
            total += extra
        assert euros == sum(v for v in self.subcosts.values()), (
            euros,
            list(self.subcosts.values()),
            sum(v for v in self.subcosts.values()),
        )


class CurrentCosting(EPUBased):
    name = "epu-based"
    minimum_area = config("minimum_area") / (360 * 180)

    def reference_grid(self, request):
        return (0.1125, 1280, 1279)

    def compute_epus(self, request, D, E, M):
        with capture_warnings(request):
            B = request.factor_B()
            V = 1
            number_of_items = request.number_of_chargeable_items()
            A = request.factor_A()
            if request.is_wave():
                landsea = request.land_sea_ratio()
            else:
                landsea = 1

            R = request.factor_R(self.reference_grid)
            frequency = request.chargeable_frequency()
            LOG.debug("EPUs for %s", request)
            LOG.debug(
                "B=%s D=%s E=%s A=%s R=%s V=%s M=%s number_of_chargeable_items=%s frequency=%s landsea=%s free=%s",
                B,
                D,
                E,
                A,
                R,
                V,
                M,
                number_of_items,
                frequency,
                landsea,
                request.free,
            )

            if A * landsea < self.minimum_area:
                log_warning_once(LOG, "Using minimum area %s. %s", config("minimum_area"), request)
                A = self.minimum_area
                landsea = 1

            return B * D * E * A * R * V * M * number_of_items * frequency * landsea


class Costing:
    def __init__(self, requests, coster_class=Coster):
        self.totals = coster_class()
        self.totals.add(*requests)

        self.per_target = defaultdict(coster_class)
        self.per_group = defaultdict(coster_class)
        self.per_category = defaultdict(coster_class)
        self.per_user = defaultdict(coster_class)
        self.per_destination = defaultdict(coster_class)
        for r in progress(requests, "Sub-totals"):
            self.per_target[r.tag].add(r)
            self.per_group[r.group].add(r)
            self.per_category[r.category].add(r)
            self.per_user[r.user].add(r)
            self.per_destination[r.destination].add(r)

    def as_dict(self):
        result = {
            "version": __version__,
            "utc_date": datetime.datetime.utcnow().isoformat().split(".")[0],
        }

        if self.per_category:
            per_category = result["per_category"] = {}
            for category, coster in sorted(self.per_category.items()):
                per_category[category] = coster.as_dict()

        if self.per_user:
            per_user = result["per_user"] = {}
            for user, coster in sorted(self.per_user.items()):
                per_user[user] = coster.as_dict()

        if self.per_destination:
            per_destination = result["per_destination"] = {}
            for destination, coster in sorted(self.per_destination.items()):
                per_destination[destination] = coster.as_dict()

        per_target = result["per_target"] = {}
        for target, coster in sorted(self.per_target.items()):
            per_target[target] = coster.as_dict()

        per_group = result["per_group"] = {}
        for group, coster in sorted(self.per_group.items()):
            per_group[group] = coster.as_dict()

        self.totals.update_subcosts(self.per_group)

        result["total"] = self.totals.as_dict()

        result["max_charge_limit"] = self.max_charge_limit
        result["max_charge"] = self.totals.euros >= result["max_charge_limit"]

        return result

    @property
    def chargeable_high_frequency(self):
        hf = self.per_group.get("high-frequency")
        if hf is None:
            return False
        return hf.euros > 0

    @property
    def max_charge_limit(self):
        if self.chargeable_high_frequency:
            return config("max-charge-high-frequency")
        return config("max-charge-core")

    def summary(
        self,
        *,
        detailed=False,
        show_groups=False,
        show_targets=False,
        show_categories=False,
        show_users=False,
        show_destinations=False,
    ):
        print("Version   :", __version__)
        print("Date (UTC):", datetime.datetime.utcnow().isoformat().split(".")[0])
        print()
        if detailed:
            minimum_area = config("minimum_area") / (360 * 180)

            for target, coster in sorted(self.per_target.items()):
                print(target)
                print()

                for r in coster.requests:
                    wave = r.is_wave()
                    with capture_warnings(r):
                        frequency, use = r.explain_frequency()
                        print("   ", r.summary())
                        print("      subset:          ", r.subset)
                        print(
                            "      representation:  ",
                            f"{r.repres.name} ({r.repres.details()})",
                        )
                        print(
                            "      reference_grid:  ",
                            r.reference_grid(coster.reference_grid),
                        )
                        print("      estimated volume:", bytes(r.estimated_volume()))
                        if use is None:
                            print("      frequency:       ", r.frequency())
                        else:
                            print(
                                "      frequency:       ",
                                r.frequency(),
                                "=",
                                frequency,
                                "*",
                                plural(use, "day"),
                            )
                        print(
                            "      fields:          ",
                            "{:,}".format(r.number_of_fields()),
                        )
                        print(
                            "      explain fields:  ",
                            r.explain_fields(),
                        )

                        if use is None:
                            print(
                                "      yearly fields:   ",
                                "{:,}".format(r.number_of_fields() * r.frequency()),
                                "=",
                                "{:,}".format(r.number_of_fields()),
                                "*",
                                r.frequency(),
                            )
                        else:
                            print(
                                "      yearly fields:   ",
                                "{:,}".format(r.number_of_fields() * r.frequency()),
                                "=",
                                "{:,}".format(r.number_of_fields()),
                                "*",
                                frequency,
                                "*",
                                plural(use, "day"),
                            )
                        print(
                            "      items:           ",
                            "{:,}".format(r.number_of_chargeable_items()),
                        )
                        print(
                            "      explain items:   ",
                            r.explain_items(),
                        )
                        D, E, _ = coster.factors(r)
                        print(
                            "      factors:         ",
                            f"B={r.factor_B()}",
                            f"A={r.factor_A():g}",
                            f"R={r.factor_R(coster.reference_grid):g}",
                            f"E={E}",
                            f"D={D}",
                        )
                        print(
                            "      explain A:       ",
                            r.explain_A(),
                        )
                        print(
                            "      explain R:       ",
                            r.explain_R(coster.reference_grid),
                        )
                        if wave:
                            if r.factor_A() * r.land_sea_ratio() >= minimum_area:
                                print(
                                    "      land/sea ratio:",
                                    "  {:g}".format(r.land_sea_ratio()),
                                )
                            else:
                                print(
                                    "      land/sea ratio:",
                                    "  {:g}".format(r.land_sea_ratio()),
                                    "(ignored due to minimum area)",
                                )

                        if wave and (r.factor_A() * r.land_sea_ratio() >= minimum_area):
                            print(
                                "      explain EPUs:    ",
                                r.factor_B(),
                                "*",
                                "{:g}".format(r.factor_A()),
                                "*",
                                "{:g}".format(r.land_sea_ratio()),
                                "*",
                                "{:g}".format(r.factor_R(coster.reference_grid)),
                                "*",
                                E,
                                "*",
                                D,
                                "*",
                                r.number_of_chargeable_items(),
                                "*",
                                r.frequency(),
                                "=",
                                "{:g}".format(
                                    r.factor_B()
                                    * r.factor_A()
                                    * r.factor_R(coster.reference_grid)
                                    * E
                                    * D
                                    * r.land_sea_ratio()
                                    * r.number_of_chargeable_items()
                                    * r.frequency()
                                ),
                            )
                        else:
                            print(
                                "      explain EPUs:    ",
                                r.factor_B(),
                                "*",
                                "{:g}".format(r.factor_A()),
                                "*",
                                "{:g}".format(r.factor_R(coster.reference_grid)),
                                "*",
                                E,
                                "*",
                                D,
                                "*",
                                r.number_of_chargeable_items(),
                                "*",
                                r.frequency(),
                                "=",
                                "{:g}".format(
                                    r.factor_B()
                                    * r.factor_A()
                                    * r.factor_R(coster.reference_grid)
                                    * E
                                    * D
                                    * r.number_of_chargeable_items()
                                    * r.frequency()
                                ),
                            )

                        if r.free:
                            print("      free:            ", r.free)
                        print("      group:           ", r.group)
                        if r.user:
                            print("      user:            ", r.user)
                        if r.category:
                            print("      category:        ", r.category)
                        if r.destination:
                            print("      destination:     ", r.destination)
                        if r.lineno:
                            print("      file/line:       ", r.lineno)
                    print("      splits:          ", r._attributes.get("split", []))
                    for w in r.warnings():
                        print("      WARNING:         ", w)
                    print()

        if detailed or show_categories:
            for category, coster in sorted(self.per_category.items()):
                if category is not None:
                    coster.summary(f"Total for category '{category}':")

        if detailed or show_users:
            for user, coster in sorted(self.per_user.items()):
                if user is not None:
                    coster.summary(f"Total for user '{user}':")

        if detailed or show_destinations:
            for destination, coster in sorted(self.per_destination.items()):
                if destination is not None:
                    coster.summary(f"Total for destination '{destination}':")

        if detailed or show_targets:
            for target, coster in sorted(self.per_target.items()):
                coster.summary(f"Total for target '{target}':")

        if detailed or show_groups:
            for group, coster in sorted(self.per_group.items()):
                coster.summary(f"Total for group '{group}':")

        self.totals.update_subcosts(self.per_group)

        self.totals.summary("Grand total:", self.max_charge_limit)

    def _rows(
        self,
        by_groups=False,
        by_targets=False,
        by_categories=False,
        by_users=False,
        by_destinations=False,
    ):
        import csv

        rows = []
        ok = True
        filter_commercial = config("commercial")

        def _(collection, per_collection, categories=None, default={}):
            for name, coster in sorted(per_collection.items()):
                r = {collection: name}
                if categories:
                    r.update(categories.get(name, default))
                r.update(coster.as_dict())
                r["max_charge_limit"] = self.max_charge_limit
                r["max_charge"] = coster.euros >= self.max_charge_limit
                r["actual_charge"] = (
                    self.max_charge_limit if coster.euros >= self.max_charge_limit else int(coster.euros)
                )

                if filter_commercial is not None:
                    if r.get("commercial") is not filter_commercial:
                        continue

                rows.append(r)

        if by_categories and ok:
            ok = False
            _("category", self.per_category)

        if by_targets and ok:
            ok = False
            _("target", self.per_target)

        if by_groups and ok:
            ok = False
            _("group", self.per_group)

        if by_users and ok:
            ok = False
            # Load categories
            categories = {}
            default = {}
            path = config("categories")
            if path:
                default = dict(category="unknown", commercial="unknown")
                categories = defaultdict(set)
                with open(path) as csvfile:
                    for row in csv.reader(csvfile, delimiter=","):
                        categories[row[2]].add(row[1])
                for k, v in list(categories.items()):
                    categories[k] = dict(
                        category=", ".join(sorted(v)),
                        commercial=any(commercial(x) for x in v),
                    )
            _("user", self.per_user, categories, default)

        if by_destinations or ok:  # The 'or' is not a typo
            # Load categories
            categories = {}
            default = {}
            path = config("categories")
            if path:
                default = dict(category="unknown", user="unknown", commercial="unknown")
                with open(path) as csvfile:
                    for row in csv.reader(csvfile, delimiter=","):
                        categories[row[0]] = dict(
                            category=row[1],
                            user=row[2],
                            commercial=commercial(row[1]),
                        )

            _("destination", self.per_destination, categories, default)

        return rows

    def html(self):
        pass

    def csv(
        self,
        file=sys.stdout,
        by_groups=False,
        by_targets=False,
        by_categories=False,
        by_users=False,
        by_destinations=False,
    ):
        import csv

        rows = self._rows(
            by_groups=by_groups,
            by_targets=by_targets,
            by_categories=by_categories,
            by_users=by_users,
            by_destinations=by_destinations,
        )

        fieldnames = list(rows[0].keys())

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    def xlsx(
        self,
        path="ecquote.xlsx",
        by_groups=False,
        by_targets=False,
        by_categories=False,
        by_users=False,
        by_destinations=False,
    ):
        import xlsxwriter

        rows = self._rows(
            by_groups=by_groups,
            by_targets=by_targets,
            by_categories=by_categories,
            by_users=by_users,
            by_destinations=by_destinations,
        )

        fieldnames = list(rows[0].keys())
        workbook = xlsxwriter.Workbook(path)
        worksheet = workbook.add_worksheet()

        def title(s):
            s = s.replace("_", " ")
            return s[0].upper() + s[1:]

        header = workbook.add_format(
            {
                "bold": True,
                "center_across": True,
                "bottom": True,
            }
        )
        for col, fieldname in enumerate(fieldnames):
            worksheet.write(0, col, title(fieldname), header)

        class StrFormat:
            def __init__(self, name, workbook):
                self.format = None
                self.width = len(name)

            def add(self, value):
                self.width = max(self.width, len(value))

        class IntFormat:
            def __init__(self, name, workbook):
                self.format = workbook.add_format()
                self.format.set_num_format(3)
                self.width = len(name)

            def add(self, value):
                self.width = max(self.width, (len(str(value)) + 2) // 3 * 4)

        class BoolFormat:
            def __init__(self, name, workbook):
                self.format = None
                self.width = len(name)

            def add(self, value):
                pass

        class FloatFormat:
            def __init__(self, name, workbook):
                self.format = None
                self.width = len(name)

            def add(self, value):
                pass

        formats = {
            str: StrFormat,
            int: IntFormat,
            bool: BoolFormat,
            float: FloatFormat,
        }

        def cell_formats(colname, value):
            if colname not in formats:
                try:
                    formats[colname] = formats[type(value)](colname, workbook)
                except KeyError:
                    print(colname, value, type(value))
                    raise
            formats[colname].add(value)
            return formats[colname].format

        for row, values in enumerate(rows):
            for col, fieldname in enumerate(fieldnames):
                value = values.get(fieldname)
                worksheet.write(row + 1, col, value, cell_formats(fieldname, value))

        for col, fieldname in enumerate(fieldnames):
            # worksheet.write(0, col, fieldname)
            worksheet.set_column(col, col, formats[fieldname].width * 0.9)

        workbook.close()


def costing(requests):
    return Costing(requests, CurrentCosting)
