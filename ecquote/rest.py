#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
import traceback

from flask import Flask, jsonify, request

from . import __version__
from .cart import Cart
from .resources import config

application = Flask(__name__)


@application.route("/health")
def health():
    return ""


@application.route("/version")
def version():
    return __version__


@application.route("/quote/<req>", methods=["GET"])
def quote(req):
    config("strict-mode", True)
    try:
        cart = Cart.from_strings(req)
        return jsonify(cart.costing())
    except Exception as e:
        return jsonify(
            dict(
                error=dict(
                    message=str(e),
                    type=e.__class__.__name__,
                    traceback=traceback.format_exc(),
                )
            )
        )


@application.route("/costing", methods=["POST"])
def costing():
    config("strict-mode", True)
    try:
        cart = Cart.from_json(request.get_json(force=True))
        return jsonify(cart.costing())
    except Exception as e:
        return jsonify(
            dict(
                error=dict(
                    message=str(e),
                    type=e.__class__.__name__,
                    traceback=traceback.format_exc(),
                )
            )
        )


@application.route("/sizes", methods=["POST"])
def sizes():
    config("strict-mode", True)
    try:
        cart = Cart.from_json(request.get_json(force=True), group_by="stream-type")
        return jsonify(cart.costing())
    except Exception as e:
        return jsonify(
            dict(
                error=dict(
                    message=str(e),
                    type=e.__class__.__name__,
                    traceback=traceback.format_exc(),
                )
            )
        )


def run(args):
    application.run(debug=True, threaded=False, processes=10)
