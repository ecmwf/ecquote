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
import warnings
from contextlib import contextmanager

import yaml

from .utils import cached_function

LOG = logging.getLogger(__name__)


OVERLAY = None


def set_overlay(overlay):
    global OVERLAY
    OVERLAY = overlay
    if not os.path.exists(OVERLAY):
        warnings.warn(f"Overlay directoty does not exist: {OVERLAY}")


def _resource_path(root, name):
    full = os.path.join(root, name)
    if os.path.exists(full):
        return full
    for ext in (".yaml", ".json", ".diss"):
        if os.path.exists(full + ext):
            return full + ext
    return None


def resource_path(name):
    if OVERLAY is not None:
        path = _resource_path(OVERLAY, name)
        if path is not None:
            warnings.warn(f"Using overlay file {path}")
            return path

    path = _resource_path(os.path.join(os.path.dirname(__file__), "resources"), name)

    if path is None:
        raise ValueError("Resource not found: '%s'" % name)

    return path


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
