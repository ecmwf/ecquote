#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import json
import logging
import os
from contextlib import contextmanager

import yaml

from .utils import cached_function

LOG = logging.getLogger(__name__)


def resource_path(name):
    full = os.path.join(os.path.dirname(__file__), "resources", name)
    if os.path.exists(full):
        return full
    for ext in (".yaml", ".json", ".diss"):
        if os.path.exists(full + ext):
            return full + ext

    raise ValueError("Resource not found: '%s'" % name)


@cached_function
def resource(name):
    path = resource_path(name)
    with open(path) as f:
        if path.endswith(".yaml"):
            return yaml.safe_load(f)
        else:
            return json.load(f)


TAG = object()
CONFIG = None


def config(name, value=TAG):
    global CONFIG
    if CONFIG is None:
        CONFIG = resource("config")
    if value is TAG:
        return CONFIG[name]
    else:
        prev = CONFIG[name]
        CONFIG[name] = value
        return prev


@contextmanager
def tmp_config(name, value):
    save = config(name, value)
    try:
        yield
    finally:
        config(name, save)
